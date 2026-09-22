from __future__ import annotations

import shlex
import time
import yaml
from importlib.resources import files
from pathlib import Path


def resolve_config_file(config_file: str | Path) -> Path:
    """Resolve a config name from config/, or an explicit relative/absolute path."""
    path = Path(config_file).expanduser()

    ## allow short names such as "qr" instead of "qr.yaml"
    if not path.suffix:
        path = path.with_suffix('.yaml')

    if path.is_absolute():
        return path.resolve()

    ## bare names are looked up in the current workspace's config directory
    if path.parent == Path('.'):
        return (Path.cwd() / 'config' / path).resolve()
    return (Path.cwd() / path).resolve()


def resolve_sidecar_command(command: str, workspace_root: Path) -> str:
    """Resolve the first token when it names a sidecar path or Python script."""

    ## keep sidecar arguments untouched while resolving only the executable
    executable, space, arguments = command.partition(' ')
    script = Path(executable).expanduser()

    ## use absolute paths directly, local paths from the workspace, and bare Python filenames from genomstack's common sidecars
    if script.is_absolute():
        resolved = script
    elif script.parent != Path('.'):
        resolved = (workspace_root / script).resolve()
    elif script.suffix == '.py':
        resolved = Path(str(files('sidecars') / script.name))
    else:
        return command

    ## Python files are scripts rather than executable commands themselves
    executable = shlex.quote(str(resolved))
    if resolved.suffix == '.py':
        executable = f'python3 {executable}'

    return executable + (space + arguments if space else '')


class AttrDict(dict):
    """Makes dict accessible by attributes.
    Made partly after https://stackoverflow.com/a/1639632/6494418
    """

    def __init__(self, dictionary):
        for key in dictionary:
            self.__setitem__(key, dictionary[key])

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            super(AttrDict, self).__setitem__(key, AttrDict(value))
        elif isinstance(value, list):
            super(AttrDict, self).__setitem__(key, [AttrDict(v) if isinstance(v, dict) else v for v in value])
        else:
            super(AttrDict, self).__setitem__(key, value)
        super(AttrDict, self).__setattr__(key, self[key])

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


class Config(AttrDict):
    def __init__(self, config_file: str | Path):
        ## establish the workspace from the resolved configuration path
        self.config_file = resolve_config_file(config_file)
        if self.config_file.parent.name != 'config':
            raise ValueError(f'Configuration must live in a workspace config/ directory: {self.config_file}')
        self.root = self.config_file.parent.parent

        ## load the YAML tree and expose it through attributes
        with open(self.config_file, 'r') as f:
            yaml_dict = yaml.safe_load(f)
        super(Config, self).__init__(yaml_dict)

        ## normalize optional fields
        self.plugin_paths = self.get('plugin_paths') or []
        self.remap = self.get('remap') or {}
        self.external_publishers = self.get('external_publishers') or {}
        self.sidecars = self.get('sidecars') or {}
        self.ros2_bag_topics = self.get('ros2_bag_topics') or []

        ## derive values shared by component wrappers
        self.inertial.J = [self.inertial.Jxx, 0.0, 0.0, 0.0, self.inertial.Jyy, 0.0, 0.0, 0.0, self.inertial.Jzz]

        ## resolve paths
        self.tmp_path = Path(self.tmp_path)

        if type(self.plugin_paths) == str:
            self.plugin_paths = [self.plugin_paths]
        self.plugin_paths = map(Path, self.plugin_paths)

        if 'rotorcraft' in self.components:
            self.components.rotorcraft.calib_file = self.root / 'calib' / self.components.rotorcraft.calib

        self.log_dir = self.root / 'logs' / f'{time.strftime("%y%m%d_%H%M%S")}_{self.config_file.stem}'

        for name, command in self.sidecars.items():
            self.sidecars[name] = resolve_sidecar_command(command, self.root)
