import os
from genomstack import RobotIO

class Mission:
    def __init__(self, io: RobotIO):
        self.io = io

    ## log helpers
    def start_logs(self) -> None:
        print('start log')
        for c in self.io.components.values():
            c.start_log()

    def stop_logs(self) -> None:
        print('stop log')
        for c in self.io.components.values():
            c.stop_log()
        for f in [f for f in os.listdir('/tmp/') if f.endswith('log')]:
            os.rename(f'/tmp/{f}', f'{self.io.cfg.log_dir}/{f}')

    ## mission helpers
    def spin(self) -> None:
        print(f'spinning...')
        self.start_logs()
        self.io.components['rotorcraft'].call('start')

    def start(self, prompt=False) -> None:
        if prompt:
            input('start?')
        print(f'starting...')
        self.io.components['rotorcraft'].call('servo', ack=True)
        self.io.components['maneuver'].call('set_current_state')
        self.io.components['maneuver'].call('take_off', 0.25, 5, ack=True)
        self.io.components['uavpos'].call('servo', ack=True)
        self.io.components['uavatt'].call('servo', ack=True)
        print('done')

    def takeoff(self, z=0.6, duration=0, prompt=False) -> None:
        if prompt:
            input('takeoff?')
        print(f'takeoff: {z:.2f} [m]')
        self.io.components['maneuver'].call('take_off', z, duration, ack=True)

    def goto(self, x, y, z, yaw, duration=0, prompt=False) -> None:
        if prompt:
            input('goto?')
        print(f'goto: {x:.2f} {y:.2f} {z:.2f} [m] -- {yaw:.2f} [rad] -- duration {duration}s')
        self.io.components['maneuver'].call('goto', x, y, z, yaw, duration, ack=True)

    def land(self, z=0.25, duration=0, prompt=False) -> None:
        if prompt:
            input('land?')
        print(f'landing: {z:.2f} [m]')
        self.io.components['maneuver'].call('take_off', z, duration, ack=True)

    def stop(self, prompt=False) -> None:
        if prompt:
            input('stop?')
        self.io.components['rotorcraft'].call('stop')
        self.stop_logs()
