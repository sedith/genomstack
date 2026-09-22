from .config import Config
from importlib.resources import files
from pathlib import Path


## workspace configuration completion
def config_completer(prefix, **_kwargs):
    config_dir = Path.cwd() / 'config'
    if not config_dir.is_dir():
        return []
    return sorted(path.stem for path in config_dir.glob('*.yaml') if path.stem.startswith(prefix))


## sidecar completion from configuration, workspace, and package
def sidecar_completer(prefix, parsed_args, **_kwargs):
    names = set()

    ## include names declared by the selected workspace configuration
    config_arg = getattr(parsed_args, 'config', None)
    if config_arg:
        try:
            names.update(Config(config_arg).sidecars)
        except (FileNotFoundError, ValueError):
            pass

    ## include workspace-local sidecars
    local_dir = Path.cwd() / 'sidecars'
    if local_dir.is_dir():
        names.update(path.stem for path in local_dir.glob('*.py') if path.name != '__init__.py')

    ## include common sidecars installed with genomstack
    names.update(path.name.removesuffix('.py') for path in files('sidecars').iterdir() if path.name.endswith('.py') and path.name != '__init__.py')
    return sorted(name for name in names if name.startswith(prefix))


## workspace ROS launch-file completion
def ros_launch_completer(prefix, parsed_args, **_kwargs):
    config_arg = getattr(parsed_args, 'config', None)
    try:
        workspace_root = Config(config_arg).root if config_arg else Path.cwd()
    except (FileNotFoundError, ValueError):
        workspace_root = Path.cwd()

    launch_dir = workspace_root / 'ros' / 'launch'
    if not launch_dir.is_dir():
        return []
    return sorted(path.stem for path in launch_dir.glob('*.py') if path.stem.startswith(prefix))
