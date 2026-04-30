
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from genomstack import RobotIO, Config
from genomstack.utils import quat2euler


def jacobian_euler2quat(q):
    roll, pitch, yaw = quat2euler(q)

    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)

    J = np.zeros((4, 3))

    ## derivatives wrt roll
    J[0, 0] = 0.5 * (-sr * cp * cy + cr * sp * sy)
    J[1, 0] = 0.5 * ( cr * cp * cy + sr * sp * sy)
    J[2, 0] = 0.5 * (-sr * sp * cy + cr * cp * sy)
    J[3, 0] = 0.5 * (-sr * cp * sy - cr * sp * cy)

    ## derivatives wrt pitch
    J[0, 1] = 0.5 * (-cr * sp * cy + sr * cp * sy)
    J[1, 1] = 0.5 * (-sr * sp * cy - cr * cp * sy)
    J[2, 1] = 0.5 * ( cr * cp * cy - sr * sp * sy)
    J[3, 1] = 0.5 * (-cr * sp * sy - sr * cp * cy)

    ## derivatives wrt yaw
    J[0, 2] = 0.5 * (-cr * cp * sy + sr * sp * cy)
    J[1, 2] = 0.5 * (-sr * cp * sy - cr * sp * cy)
    J[2, 2] = 0.5 * (-cr * sp * sy + sr * cp * cy)
    J[3, 2] = 0.5 * ( cr * cp * cy + sr * sp * sy)

    return J


def odom_to_pom_measure(msg: Odometry, cov: dict) -> dict:
    s = msg.header.stamp
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    v = msg.twist.twist.linear
    w = msg.twist.twist.angular

    J = jacobian_euler2quat([q.w, q.x, q.y, q.z])
    cov_q = J @ cov['eul'] @ J.T

    return {
        'measure': {
            'ts': {'sec': s.sec, 'nsec': s.nanosec},
            'intrinsic': 0,
            'pos': {'x': p.x, 'y': p.y, 'z': p.z},
            'att': {'qw': q.w, 'qx': q.x, 'qy': q.y, 'qz': q.z},
            'vel': {'vx': v.x, 'vy': v.y, 'vz': v.z},
            'avel': {'wx': w.x, 'wy': w.y, 'wz': w.z},
            'acc': None,
            'aacc': None,
            'pos_cov': {'cov': cov['p']},
            'att_cov': {'cov': list(cov_q[np.tril_indices(4)])},
            'att_pos_cov': None,
            'vel_cov': {'cov': cov['v']},
            'avel_cov': {'cov': cov['w']},
            'acc_cov': None,
            'aacc_cov': None,
        }
    }


def main():
    if len(sys.argv) != 2:
        print('usage: python3 ros2/lio_relay.py <config name>.yaml')
        return 1

    config_arg = sys.argv[1]
    io = RobotIO(config_arg)

    topic = '/rko_lio/odometry'
    publisher_name = 'lidar'
    std_p = 0.001
    std_eul = 0.001
    std_v = 0.1
    std_w = 0.1

    cov = {}
    cov['p'] = list((np.eye(3) * std_p ** 2)[np.tril_indices(3)])
    cov['v'] = list((np.eye(3) * std_v ** 2)[np.tril_indices(3)])
    cov['w'] = list((np.eye(3) * std_w ** 2)[np.tril_indices(3)])
    cov['eul'] = np.eye(3) * std_eul ** 2

    rclpy.init()
    node = Node('lio_relay')

    def callback(msg):
        print(msg.pose.pose.position)
        io.publish(publisher_name, odom_to_pom_measure(msg, cov))

    node.create_subscription(
        Odometry,
        topic,
        callback,
        10,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
