from .config import Config, load_config
from .components import *
from .runtime import Runtime
import os


class Robot:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.runtime = Runtime(cfg)

        if cfg.mocap.model == 'qualisys':
            self.mocap = Qualisys(cfg)
        elif cfg.mocap.model == 'optitrack':
            self.mocap = Optitrack(cfg)
        self.rotorcraft = Rotorcraft(cfg)
        self.pom = Pom(cfg)
        self.uavpos = UavPos(cfg)
        self.uavatt = UavAtt(cfg)
        self.maneuver = Maneuver(cfg)

        self.components = [
            self.rotorcraft,
            self.mocap,
            self.pom,
            self.uavpos,
            self.uavatt,
            self.maneuver,
        ]

    def setup(self):
        print(f'init genomix...')
        self.runtime.connect()

        for c in self.components:
            print(f'loading {c.name}...')
            self.runtime.load(c)
            c.setup()
        print('done')

    def start_logs(self):
        print('start log')
        for c in self.components:
            c.start_log()

    def stop_logs(self):
        print('stop log')
        for c in self.components:
            c.stop_log()
        for f in [f for f in os.listdir('/tmp/') if f.endswith('log')]:
            os.rename(f'/tmp/{f}', f'{self.cfg.log_dir}/{f}')

    def spin(self):
        print(f'spinning...')
        self.start_logs()
        self.rotorcraft.call('start')

    def start(self, prompt=False):
        if prompt:
            input('start?')
        print(f'starting...')
        self.rotorcraft.call('servo', ack=True)
        self.maneuver.call('set_current_state')
        self.maneuver.call('take_off', 0.25, 5, ack=True)
        self.uavpos.call('servo', ack=True)
        self.uavatt.call('servo', ack=True)
        print('done')

    def takeoff(self, z=0.6, duration=0, prompt=False):
        if prompt:
            input('takeoff?')
        print(f'takeoff: {z:.2f} [m]')
        self.maneuver.call('take_off', z, duration, ack=True)

    def goto(self, x, y, z, yaw, duration=0, prompt=False):
        if prompt:
            input('goto?')
        print(f'goto: {x:.2f} {y:.2f} {z:.2f} [m] -- {yaw:.2f} [rad] -- duration {duration}s')
        self.maneuver.call('goto', x, y, z, yaw, duration, ack=True)

    def land(self, z=0.25, duration=0, prompt=False):
        if prompt:
            input('land?')
        print(f'landing: {z:.2f} [m]')
        self.maneuver.call('take_off', z, duration, ack=True)

    def stop(self, prompt=False):
        if prompt:
            input('stop?')
        self.rotorcraft.call('stop')
        self.stop_logs()
