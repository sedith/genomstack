import os
import subprocess
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from .components import *
from .config import Config
from .external_publisher import ExternalPublisher
from .genomix import Genomix
from .process import is_localhost, shell_path
from .rosutils.rosbag_recorder import RosbagRecorder


@contextmanager
def silence(enabled: bool = True):
    if not enabled:
        yield
        return

    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            yield


## robot runtime facade
class RobotIO:
    COMPONENT_CLASSES = {
        'rotorcraft': Rotorcraft,
        'optitrack': Optitrack,
        'qualisys': Qualisys,
        'pom': Pom,
        'uavpos': UavPos,
        'uavatt': UavAtt,
        'maneuver': Maneuver,
        'phynt': Phynt,
        'nhfc': Nhfc,
        'gazebocam': GazeboCam,
        'arucotag': ArucoTag,
    }

    def __init__(self, cfg: str, silent: bool = False):
        self.silent = silent

        with silence(self.silent):
            ## load configuration and initialize the genom connection
            self.cfg = Config(cfg)
            self.genonix = Genomix(self.cfg)

            ## initialize component classes
            self.components = {}
            self.publishers = {}

            for name, component_cfg in self.cfg.components.items():
                component_type = getattr(component_cfg, 'type', name)
                component_cls = self.COMPONENT_CLASSES[component_type]
                component = component_cls(self.cfg, name)
                self.components[name] = component

            ## connect to genom and load component handles
            print(f'init genomix...')
            self.genonix.connect()

            for c in self.components.values():
                print(f'loading {c.name}...')
                self.genonix.load(c)

            ## initialize configured external publishers
            for name, extpub_cfg in self.cfg.external_publishers.items():
                print(f'init external pub {name}...')
                extpub = ExternalPublisher(self.cfg, name, io=self)
                self.publishers[name] = extpub

            ## enable ROS bag recording only when topics are configured
            topics = getattr(self.cfg, 'ros2_bag_topics', None)
            if topics:
                self.rosbag = RosbagRecorder(self.cfg)
            else:
                self.rosbag = None

            self.logging = False
            print('IO init done')

    ## component lifecycle
    def setup_components(self) -> None:
        """Configure and wire all components."""
        if self.silent:
            print('warning: configuring components from a silent RobotIO instance')
        for c in self.components.values():
            print(f'setup {c.name}...')
            c.setup()

    def start_components(self) -> None:
        indexed = enumerate(self.components.values())
        components = sorted(indexed, key=lambda item: (item[1].START_ORDER, item[0]))

        for _, component in components:
            print(f'start {component.name}...')
            component.start()

    ## component and publisher data access
    def read(self, component_name: str, port: str) -> dict:
        port, *subport = port.split('/')
        return self.components[component_name].call(port, *subport)

    def publish(self, publisher_name: str, msg: dict) -> None:
        self.publishers[publisher_name].publish(msg)

    ## logging + rosbag helpers
    def start_logs(self) -> None:
        if self.logging:
            return
        print('start log')

        for component in self.components.values():
            component.start_log()

        if self.rosbag is not None:
            self.rosbag.start_log()

        self.logging = True

    def stop_logs(self) -> None:
        if not self.logging:
            return
        print('stop log')

        for component in self.components.values():
            component.stop_log()

        if self.rosbag is not None:
            self.rosbag.stop_log()

        self.logging = False

    def export_logs(self) -> None:
        self.cfg.log_dir.mkdir(parents=True, exist_ok=True)

        ## move local logs directly or copy remote logs before removing them
        if is_localhost(self.cfg.host):
            for path in self.cfg.tmp_path.expanduser().glob('*'):
                os.rename(str(path), self.cfg.log_dir / path.name)
        else:
            subprocess.run(
                ['scp', '-r', f'{self.cfg.host}:{self.cfg.tmp_path}/*', str(self.cfg.log_dir)],
                check=True,
            )
            subprocess.run(
                ['ssh', self.cfg.host, f'rm -r {shell_path(self.cfg.tmp_path)}/*'],
                check=True,
            )
