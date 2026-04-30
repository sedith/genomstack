#!/usr/bin/env python3
import os
import shlex
import sys
from pathlib import Path
from genomstack.config import Config
from genomstack.utils import is_localhost

ROOT = Path(__file__).resolve().parents[1]
ROS_CONFIG_DIR = ROOT / 'ros2' / 'config'
SOURCED_ENV = 'GENOMSTACK_ROS2_SOURCED'
REMOTE_ENV = 'GENOMSTACK_REMOTE_EXEC'

## import ros stuff only after sourcing
if os.environ.get(SOURCED_ENV) == '1':
    from launch import LaunchService
    from launch import LaunchDescription
    from launch_ros.actions import Node


## relaunchers
def relaunch_remote(cfg: Config, config_arg: str) -> None:
    remote_cmd = (
        f'source ~/.onepiece.bashrc && '
        f'cd {cfg.ros2.workspace} && '
        f'export {REMOTE_ENV}=1 && '
        f'exec python3 ros2/launcher.py {shlex.quote(config_arg)}'
    )

    os.execvp('ssh', [
        'ssh',
        '-t',
        cfg.host,
        f'bash -lc {shlex.quote(remote_cmd)}',
    ])


def relaunch_with_ros_env(cfg: Config) -> None:
    setup_cmds = []
    for setup in cfg.ros2.setup:
        setup = os.path.expandvars(os.path.expanduser(setup))

        setup_path = Path(setup)
        if not setup_path.is_absolute():
            setup_path = cfg.root / setup_path

        setup_cmds.append(f'source {shlex.quote(str(setup_path))}')

    env_cmds = [
        f'export {SOURCED_ENV}=1',
        'export ROS_LOCALHOST_ONLY=0',
    ]

    if 'domain_id' in cfg.ros2:
        env_cmds.append(f'export ROS_DOMAIN_ID={shlex.quote(str(cfg.ros2["domain_id"]))}')

    cmd = ' && '.join(setup_cmds + env_cmds)
    cmd += ' && exec ' + ' '.join(
        shlex.quote(arg) for arg in [sys.executable] + sys.argv
    )

    os.execv('/bin/bash', ['bash', '-lc', cmd])


## node helpers
def node_tf_static():
    return [
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_lidar_livox_imu',
            arguments=[
                '0.011', '0.02329', '-0.04412',
                '0.0', '0.0', '0.0',
                'livox_lidar', 'livox_imu',
            ],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_rko',
            arguments=[
                '--x', '0',
                '--y', '0',
                '--z', '0',
                '--roll', '0',
                '--pitch', '0',
                '--yaw', '0',
                '--frame-id', 'body_rko',
                '--child-frame-id', 'livox_lidar',
            ],
            output='screen',
        ),
    ]


def node_rko(use_sim_time: bool):
    return [
        Node(
            package='rko_lio',
            executable='online_node',
            name='rko_lio',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'use_sim_time': use_sim_time},
                str(ROS_CONFIG_DIR / 'rko_lio.yaml'),
            ],
        ),
    ]

def node_livox():
    return [
        Node(
            package='livox_ros_driver2',
            executable='livox_ros_driver2_node',
            name='livox_lidar_publisher',
            output='screen',
            parameters=[
                str(ROS_CONFIG_DIR / 'mid360.yaml'),
                {'user_config_path': str(ROS_CONFIG_DIR / 'mid360.json')}
            ],
        )
    ]

def node_gz_lidar():
    return [
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_lidar_imu_bridge',
            output='screen',
            arguments=[
                '/livox/lidar@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
                '/livox/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            ],
        )
    ]


def make_launch_description(cfg):
    ros_cfg = cfg.get('ros2', {})
    mode = ros_cfg.get('mode', 'none')

    actions = []

    if mode == 'livox':
        actions = node_tf_static() + node_livox() + node_rko(use_sim_time=False)

    elif mode == 'gazebo':
        actions = node_tf_static() + node_gz_lidar() + node_rko(use_sim_time=True)

    elif mode == 'none':
        pass

    else:
        raise ValueError(
            f'Unknown ros2.mode "{mode}". Expected one of: none, livox, gazebo.'
        )

    if cfg.ros2.rviz:
        print('rviz launch is not implemented yet')

    return LaunchDescription(actions)



def main():
    if len(sys.argv) != 2:
        print('usage: python3 ros2/launcher.py <config name>.yaml')
        return 1

    config_arg = sys.argv[1]
    cfg = Config(config_arg)

    if not cfg.ros2.enabled:
        print('ros2 disabled')
        return 0

    ## relaunch script if necessary
    if not is_localhost(cfg.host) and os.environ.get(REMOTE_ENV) != '1':
        relaunch_remote(cfg, config_arg)

    if os.environ.get(SOURCED_ENV) != '1':
        relaunch_with_ros_env(cfg)

    ## generate launch descriptor and run
    launch_service = LaunchService()
    launch_service.include_launch_description(make_launch_description(cfg))

    return launch_service.run()


if __name__ == '__main__':
    raise SystemExit(main())
