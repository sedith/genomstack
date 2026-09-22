#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from genomstack import Config, LocalRunner
from genomstack.arg_complete import config_completer, sidecar_completer


## command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description='Run one sidecar from a genomstack workspace configuration.',
    )
    parser.add_argument('config', help='workspace config name or path').completer = config_completer
    parser.add_argument('sidecar', help='name of the sidecar in the config').completer = sidecar_completer
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ## resolve the selected sidecar from the workspace configuration
    cfg = Config(args.config)

    if args.sidecar not in cfg.sidecars:
        available = ', '.join(cfg.sidecars) or 'none'
        raise SystemExit(f'unknown sidecar {args.sidecar!r}; configured sidecars: {available}')

    runner = LocalRunner(workspace=cfg.root, setup=cfg.setup)
    try:
        ## supervise the sidecar until shutdown
        runner.start(args.sidecar, cfg.sidecars[args.sidecar])
        runner.hang()
    except KeyboardInterrupt:
        print('stopping')
        runner.stop_all()
    except Exception as error:
        print(f'error: {error}')
        print('killing')
    finally:
        ## ensure the child process cannot outlive the runner
        runner.kill_all()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
