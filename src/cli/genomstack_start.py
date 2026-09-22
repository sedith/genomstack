#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from genomstack import Config, LocalRunner
from genomstack.arg_complete import config_completer


## command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description='Start the GenoM components and configured sidecars.',
    )
    parser.add_argument('config', help='workspace config name or path').completer = config_completer
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ## initialize the workspace runner
    cfg = Config(args.config)
    cfg.tmp_path.expanduser().mkdir(parents=True, exist_ok=True)
    runner = LocalRunner(workspace=cfg.root, setup=cfg.setup)
    delay = 0.5

    try:
        ## initialize the GenoM runtime
        runner.run('h2 end > /dev/null 2>&1', check=False)
        runner.run('h2 init', check=False, wait=delay)
        runner.start('genomixd', 'genomixd', wait=delay)

        ## start component processes
        for name, component in cfg.components.items():
            runner.start(name, f'{component.type}-pocolibs -f -i {name}', wait=delay)

        ## start the remaining configured sidecars
        for name, sidecar in cfg.sidecars.items():
            runner.start(name, sidecar, wait=delay)

        ## supervise all processes until shutdown
        print('hanging until ^C...')
        runner.hang()

    except KeyboardInterrupt:
        print('stopping')
        runner.stop_all()
    except Exception as e:
        print(f'error: {e}')
        print('killing')
    finally:
        ## force cleanup after normal or exceptional exit
        runner.kill_all()
        runner.run('h2 end', check=False)
        runner.run(f'rm ~/.*.pid-* > /dev/null 2>&1', check=False)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
