#!/usr/bin/env python3
import rclpy
import sys
import time
from genomstack import RobotIO
from genomstack.rosutils.convert import Cov, odom_to_pose_estimator
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


class LioRelay(Node):
    def __init__(self, config_arg: str, topic: str):
        super().__init__('lio_relay')

        ## connect a read-only IO facade to the configured stack
        self.io = RobotIO(config_arg, silent=True)

        ## configure the relay topic, target publisher, and rate monitoring
        self.topic = topic
        self.publisher_name = 'lidar'
        self.repub_vel = True
        self.min_rate = 9.0

        self.printed = False
        self.last_msg_time = None
        self.last_warn_time = 0.0
        # self.cov = Cov().from_stds(std_p=0.001, std_eul=0.01, std_v=0.1, std_w=0.05)
        self.cov = Cov().from_stds(std_p=0.0005, std_eul=0.005, std_v=0.05, std_w=0.025)

        ## register ROS subscription and health timer
        self.create_subscription(Odometry, self.topic, self.callback, 10)
        self.create_timer(1.0, self.check_rate)

    def callback(self, msg: Odometry):
        self.last_msg_time = time.monotonic()

        ## report the first valid pose for operator feedback
        if not self.printed:
            self.printed = True
            p = msg.pose.pose.position
            self.get_logger().info(f'first pose retrieved: {p.x:.3f}, {p.y:.3f}, {p.z:.3f}')

        ## convert and forward the odometry sample to genom
        ts = divmod(time.time_ns(), 1_000_000_000)
        data = odom_to_pose_estimator(msg, ts=ts, cov=self.cov, repub_vel=self.repub_vel)
        self.io.publish(self.publisher_name, data)

    def check_rate(self):
        ## throttle warnings when the input stream falls below its expected rate
        if self.last_msg_time is not None:
            now = time.monotonic()
            if now - self.last_msg_time > 1.0 / self.min_rate and now - self.last_warn_time > 2.0:
                self.last_warn_time = now
                self.get_logger().warn(f'{self.topic} rate below {self.min_rate:.1f} Hz')


def main():
    ## command-line arguments
    if len(sys.argv) != 3:
        print('usage: python3 -m sidecars.lio_relay <config name>.yaml <topic>')
        return 1
    config_arg = sys.argv[1]
    topic = sys.argv[2]

    ## initialize and spin the ROS node
    rclpy.init()
    node = LioRelay(config_arg, topic)

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
