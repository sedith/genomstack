#!/usr/bin/env python3
import sys

import rclpy

from genomstack import RobotIO
from genomstack.rosutils.convert import pose_estimator_to_odometry, rigid_body_to_pose_stamped
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class RvizBridge(Node):
    def __init__(self, config_arg: str, rate_hz: float = 20.0):
        super().__init__('genom_rviz_bridge')

        ## connect to GenoM and create the two ROS publishers
        self.io = RobotIO(config_arg, silent=True)
        self.pom_pub = self.create_publisher(Odometry, '/genom/pom/odometry', 10)
        self.path_pub = self.create_publisher(Path, '/genom/pom/path', 10)
        self.maneuver_pub = self.create_publisher(PoseStamped, '/genom/maneuver/desired', 10)
        self.path = Path()
        self.path.header.frame_id = 'map'
        self.timer = self.create_timer(1.0 / rate_hz, self.update)

    def update(self):
        """Publish the current POM frame and maneuver reference."""
        try:
            state = self.io.read('pom', 'frame/robot')['frame']
            odometry = pose_estimator_to_odometry(state, frame_id='map', child_frame_id='body')
            self.pom_pub.publish(odometry)

            pose = PoseStamped()
            pose.header = odometry.header
            pose.pose = odometry.pose.pose
            self.path.header.stamp = odometry.header.stamp
            self.path.poses.append(pose)
            self.path_pub.publish(self.path)
        except KeyError:
            pass
        except Exception as error:
            self.get_logger().warn(f'failed to publish pom state: {error}')

        try:
            reference = self.io.read('maneuver', 'desired')['desired']
            if not None in [reference['pos'], reference['att']]:
                self.maneuver_pub.publish(rigid_body_to_pose_stamped(reference, frame_id='map'))
        except KeyError:
            pass
        except Exception as error:
            self.get_logger().warn(f'failed to publish maneuver reference: {error}')


def main():
    ## command-line arguments
    if len(sys.argv) not in (2, 3):
        print('usage: python3 -m sidecars.rviz_bridge <config name>.yaml [rate_hz]')
        return 1

    rate_hz = float(sys.argv[2]) if len(sys.argv) == 3 else 20.0

    ## initialize and spin the ROS node
    rclpy.init()
    node = RvizBridge(sys.argv[1], rate_hz)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
