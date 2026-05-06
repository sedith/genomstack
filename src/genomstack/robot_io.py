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

        print(f'init genomix...')
        self.runtime.connect()

        for c in self.components.values():
            print(f'loading {c.name}...')
            self.runtime.load(c)

        for name, extpub_cfg in self.cfg.external_publishers.items():
            print(f'init external pub {name}...')
            extpub = ExternalPublisher(self.cfg, name, io=self)
            self.publishers[name] = extpub
        print('IO init done')

    def setup(self) -> None:
        for c in self.components.values():
            print(f'setup {c.name}...')
            c.setup()

    def read(self, component_name: str, port: str) -> dict:
        port, *subport = port.split('/')
        return self.components[component_name].call(port, *subport)

    def _component_by_type(self, gtype: str):
        """Return the first loaded component whose genomix type matches gtype."""
        for c in self.components.values():
            if c.gtype == gtype:
                return c
        raise KeyError(f'No component of type {gtype!r} found')

    def get_battery(self) -> float | None:
        """Return battery voltage in V, or None on failure."""
        raw = self._component_by_type('rotorcraft').call('get_battery')
        return raw['battery']['level']

    def get_state(self) -> dict | None:
        """Return a dict with 'pos' (x,y,z) and 'att' (qw,qx,qy,qz), or None on failure."""
        body = self._component_by_type('pom').call('frame', 'robot')['frame']
        return {
            'pos': (body['pos']['x'], body['pos']['y'], body['pos']['z']),
            'att': (body['att']['qw'], body['att']['qx'],
                    body['att']['qy'], body['att']['qz']),
        }

    def publish(self, publisher_name: str, msg: dict) -> None:
        self.publishers[publisher_name].publish(msg)
