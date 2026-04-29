from .config import Config
from .runtime import Runtime
from .components import *
from .external_publisher import ExternalPublisher


class RobotIO:
    COMPONENT_CLASSES = {
        'rotorcraft': Rotorcraft,
        'optitrack': Optitrack,
        'qualisys': Qualisys,
        'pom': Pom,
        'uavpos': UavPos,
        'uavatt': UavAtt,
        'maneuver': Maneuver,
    }

    def __init__(self, cfg: str):
        self.cfg = Config(cfg)
        self.runtime = Runtime(self.cfg)

        self.components = {}
        self.publishers = {}

        for name, component_cfg in self.cfg.components.items():
            component_type = getattr(component_cfg, 'type', name)
            component_cls = self.COMPONENT_CLASSES[component_type]
            component = component_cls(self.cfg, name, io=self)
            self.components[name] = component

        for name, extpub_cfg in self.cfg.external_publishers.items():
            extpub = ExternalPublisher(self.cfg, name, io=self)
            self.publishers[name] = extpub

    def setup(self) -> None:
        print(f'init genomix...')
        self.runtime.connect()

        for c in self.components.values():
            print(f'loading {c.name}...')
            self.runtime.load(c)
            c.setup()

        for extpub in self.publishers.values():
            print(f'init external pub {extpub.name}...')
            extpub.setup()
        print('done')

    def attach(self) -> None:
        print(f'attaching to genomix...')
        self.runtime.connect()

        for c in self.components.values():
            print(f'attaching to {c.name}...')
            self.runtime.load(c)
        print('done')

    def read(self, component_name: str, port_name: str) -> dict:
        return self.components[component_name].call(port_name)

    def publish(self, publisher_name: str, msg: dict) -> None:
        self.publishers[publisher].publish(msg)
