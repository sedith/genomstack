#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
import shlex
import sys
from genomstack import Config, LocalRunner
from genomstack.arg_complete import config_completer, ros_launch_completer


## command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Run one ROS 2 launch script from a genomstack workspace.')
    parser.add_argument('config', help='workspace config name or path').completer = config_completer
    parser.add_argument('launchfile', help='launch script name, with or without .py').completer = ros_launch_completer
    parser.add_argument('launch_args', nargs=argparse.REMAINDER, help='additional arguments passed to the launch script')
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ## resolve the launch script inside the configured workspace
    cfg = Config(args.config)
    filename = args.launchfile if args.launchfile.endswith('.py') else f'{args.launchfile}.py'
    launchfile = cfg.root / 'ros' / 'launch' / filename
    if not launchfile.is_file():
        print(f'error: ROS launch file not found: {launchfile}', file=sys.stderr)
        return 1

    ## prepare the workspace ROS configuration path
    config_dir = cfg.root / 'ros' / 'config'

    ## launch ROS with the configured setup
    commands = []
    commands.append(shlex.join([sys.executable, str(launchfile), str(config_dir), *args.launch_args]))

    runner = LocalRunner(workspace=cfg.root, setup=cfg.setup)

    try:
        runner.start('ros2', commands)
        runner.hang()
    except KeyboardInterrupt:
        print('stopping')
    finally:
        runner.stop_all()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
