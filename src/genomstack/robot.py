import os
from .config import Config
from .runtime import Runtime
from .components import *
from .external_publisher import ExternalPublisher


class Robot:
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

        self.components = []
        self.external_publishers = []

        for name, component_cfg in self.cfg.components.items():
            component_type = getattr(component_cfg, 'type', name)
            component_cls = self.COMPONENT_CLASSES[component_type]
            component = component_cls(self.cfg, name, robot=self)
            setattr(self, name, component)
            self.components.append(component)

        for name, extpub_cfg in self.cfg.external_publishers.items():
            extpub = ExternalPublisher(self.cfg, name, robot=self)
            setattr(self, name, extpub)
            self.external_publishers.append(extpub)

    def setup(self) -> None:
        print(f'init genomix...')
        self.runtime.connect()

        for c in self.components:
            print(f'loading {c.name}...')
            self.runtime.load(c)
            c.setup()

        for extpub in self.external_publishers:
            print(f'init external pub {extpub.name}...')
            extpub.setup()

        print('done')

    def start_logs(self) -> None:
        print('start log')
        for c in self.components:
            c.start_log()

    def stop_logs(self) -> None:
        print('stop log')
        for c in self.components:
            c.stop_log()
        for f in [f for f in os.listdir('/tmp/') if f.endswith('log')]:
            os.rename(f'/tmp/{f}', f'{self.cfg.log_dir}/{f}')

    def spin(self) -> None:
        print(f'spinning...')
        self.start_logs()
        self.rotorcraft.call('start')

    def start(self, prompt=False) -> None:
        if prompt:
            input('start?')
        print(f'starting...')
        self.rotorcraft.call('servo', ack=True)
        self.maneuver.call('set_current_state')
        self.maneuver.call('take_off', 0.25, 5, ack=True)
        self.uavpos.call('servo', ack=True)
        self.uavatt.call('servo', ack=True)
        print('done')

    def takeoff(self, z=0.6, duration=0, prompt=False) -> None:
        if prompt:
            input('takeoff?')
        print(f'takeoff: {z:.2f} [m]')
        self.maneuver.call('take_off', z, duration, ack=True)

    def goto(self, x, y, z, yaw, duration=0, prompt=False) -> None:
        if prompt:
            input('goto?')
        print(f'goto: {x:.2f} {y:.2f} {z:.2f} [m] -- {yaw:.2f} [rad] -- duration {duration}s')
        self.maneuver.call('goto', x, y, z, yaw, duration, ack=True)

    def land(self, z=0.25, duration=0, prompt=False) -> None:
        if prompt:
            input('land?')
        print(f'landing: {z:.2f} [m]')
        self.maneuver.call('take_off', z, duration, ack=True)

    def stop(self, prompt=False) -> None:
        if prompt:
            input('stop?')
        self.rotorcraft.call('stop')
        self.stop_logs()
