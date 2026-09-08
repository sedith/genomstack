import copy
from pathlib import Path as FilePath
import numpy as np
import xml.etree.ElementTree as ET
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from tf2_ros import StaticTransformBroadcaster
from genomstack.utils import euler2quat, euler2rot, rot2euler, rot2quat


def parse_model_rec(sdf_file, model_name, model_dir=None,
                    base_xyz=None, base_rot=None, markers=None):
    ## initialize carry-on variables
    # sdf_file = FilePath(sdf_file)
    if markers is None:
        markers = MarkerArray()
        base_xyz = np.zeros(3)
        base_rot = np.eye(3)
        model_dir = sdf_file.parent

    ## parse sdf
    root = ET.parse(sdf_file).getroot()
    if model_name is not None:
        model = root.find(f'.//model[@name="{model_name}"]')
    else:
        model = root.find('.//model')

    if model is None:
        raise ValueError(f'Model "{model_name}" not found in {sdf_file}')

    ## loop over model links
    for link in model.findall('link'):
        ## link base pose
        xyz = base_xyz.copy()
        rot = base_rot.copy()
        if (pose := link.find('pose')) is not None:
            x, y, z, r, p, yaw = map(float, pose.text.split())
            xyz += rot @ np.array([x, y, z])
            rot = rot @ euler2rot([r, p, yaw])

        ## create a marker for each visual element
        for visual in link.findall('visual'):
            if (geometry := visual.find('geometry')) is None:
                continue

            ## header and metadata common to all markers
            marker = Marker()
            marker.header.frame_id = 'body_pom'
            marker.frame_locked = True
            marker.id = len(markers.markers)
            marker.action = Marker.ADD

            ## mark rotor blades for animation
            if model.get('name') == 'mrsim-rotor' and visual.get('name') == 'blade':
                marker.ns = 'rotor_blade'
            else:
                marker.ns = 'robot_model'
                
            ## create corresponding geometry
            if (cyl := geometry.find('cylinder')) is not None:
                radius = float(cyl.findtext('radius'))
                marker.type = Marker.CYLINDER
                marker.scale.x = marker.scale.y = 2 * radius
                marker.scale.z = float(cyl.findtext('length'))
            elif (box := geometry.find('box')) is not None:
                marker.type = Marker.CUBE
                marker.scale.x, marker.scale.y, marker.scale.z = map(float, box.findtext('size').split())
            elif (sphere := geometry.find('sphere')) is not None:
                diameter = 2 * float(sphere.findtext('radius'))
                marker.type = Marker.SPHERE
                marker.scale.x = marker.scale.y = marker.scale.z = diameter
            else:
                continue

            ## visual pose
            visual_xyz = xyz.copy()
            visual_rot = rot.copy()
            if (pose := visual.find('pose')) is not None:
                x, y, z, r, p, yaw = map(float, pose.text.split())
                visual_xyz += visual_rot @ np.array([x, y, z])
                visual_rot = visual_rot @ euler2rot([r, p, yaw])

            q = rot2quat(visual_rot)
            marker.pose.position.x = float(visual_xyz[0])
            marker.pose.position.y = float(visual_xyz[1])
            marker.pose.position.z = float(visual_xyz[2])
            marker.pose.orientation.w = float(q[0])
            marker.pose.orientation.x = float(q[1])
            marker.pose.orientation.y = float(q[2])
            marker.pose.orientation.z = float(q[3])

            ## marker color
            if (diffuse := visual.findtext('material/diffuse')):
                marker.color.r, marker.color.g, marker.color.b, marker.color.a = map(float, diffuse.split())
            else:
                marker.color.r = marker.color.g = marker.color.b = 0.5
                marker.color.a = 1.0

            ## append to marker array
            markers.markers.append(marker)

    ## recursively look into all included models
    for include in model.findall('include'):
        uri = include.findtext('uri', '')
        if not uri.startswith('model://'):
            continue

        included_sdf = model_dir / uri.removeprefix('model://') / 'model.sdf'
        if not included_sdf.exists():
            print(f'Could not find included model: {included_sdf}')
            continue

        ## included model base pose
        xyz = base_xyz.copy()
        rot = base_rot.copy()
        if (pose := include.find('pose')) is not None:
            x, y, z, r, p, yaw = map(float, pose.text.split())
            xyz += rot @ np.array([x, y, z])
            rot = rot @ euler2rot([r, p, yaw])

        ## parse included model
        parse_model_rec(included_sdf, None, model_dir, xyz, rot, markers)

    ## return marker array
    return markers


class OdomPath(Node):
    def __init__(self):
        super().__init__('odom_path')

        self.path = Path()
        self.markers = parse_model_rec(FilePath('gz/lluis.sdf'), 'tx')

        self.tf_broadcaster = TransformBroadcaster(self)
        self.path_pub = self.create_publisher(Path, '/genom/pom/path', 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/genom/robot_model', 10)
        self.odom_sub = self.create_subscription(Odometry, '/genom/pom/odometry', self.odom_callback, 10)

        ## static tf
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)
        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = 'body'
        tf.child_frame_id = 'body_pom'
        tf.transform.translation.x = 0.0
        tf.transform.translation.y = 0.0
        tf.transform.translation.z = -0.#15
        tf.transform.rotation.w, tf.transform.rotation.x, tf.transform.rotation.y, tf.transform.rotation.z = euler2quat([0,0,-0.1])
        self.static_tf_broadcaster.sendTransform(tf)

        ## animate propellers
        timer_frequency = 30
        rotation_speed = 100
        self.angle_inc = 2 * np.pi * rotation_speed / timer_frequency
        self.rotor_timer = self.create_timer(1.0 / timer_frequency, self.rotate_propellers)

    def odom_callback(self, msg: Odometry):
        ## wait until pom is initialized with some odom
        if msg.pose.pose.position.x == 0.0 and msg.pose.pose.position.y == 0.0 and msg.pose.pose.position.z == 0.0:
            return

        ## publish path
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose

        self.path.poses.append(pose)
        self.path.header.frame_id = msg.header.frame_id
        self.path.header.stamp = msg.header.stamp
        self.path_pub.publish(self.path)

        # ## publish tf
        # tf = TransformStamped()
        # tf.header.stamp = msg.header.stamp
        # tf.header.frame_id = msg.header.frame_id
        # tf.child_frame_id = 'body_pom'
        # tf.transform.translation.x = msg.pose.pose.position.x
        # tf.transform.translation.y = msg.pose.pose.position.y
        # tf.transform.translation.z = msg.pose.pose.position.z
        # tf.transform.rotation = msg.pose.pose.orientation
        # self.tf_broadcaster.sendTransform(tf)


    def rotate_propellers(self):
        ## fixed rotation increment around each propeller local z axis
        c = np.cos(self.angle_inc / 2.0)
        s = np.sin(self.angle_inc / 2.0)

        for marker in self.markers.markers:
            if marker.ns == 'rotor_blade':
                q = marker.pose.orientation
                w, x, y, z = q.w, q.x, q.y, q.z
                q.w = w * c - z * s
                q.x = x * c + y * s
                q.y = y * c - x * s
                q.z = w * s + z * c

        self.marker_pub.publish(self.markers)

def main():
    rclpy.init()
    node = OdomPath()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
