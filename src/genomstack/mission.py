import os
from pathlib import Path
import subprocess
import sys
from .robot_io import RobotIO
from .utils import is_localhost

class Mission:
    def __init__(self, io: RobotIO):
        self.io = io
        self.bag_process = None

    ## log helpers
    def start_logs(self) -> None:
        print('start log')

        ## logs genom
        for c in self.io.components.values():
            c.start_log()

        ## record ros2bag
        if 'bag' in self.io.cfg.ros2:
            self.bag_process = subprocess.Popen([
                sys.executable,
                str(self.io.cfg.root / 'ros2/bag_record.py'),
                str(self.io.cfg.config_file),
            ])

    def stop_logs(self) -> None:
        print('stop log')

        ## stop logs
        for c in self.io.components.values():
            c.stop_log()

        ## stop bag record
        if self.bag_process is not None:
            self.bag_process.terminate()
            self.bag_process.wait()
            self.bag_process = None

        ## fetch files
        self.io.cfg.log_dir.mkdir(parents=True, exist_ok=True)
        if is_localhost(self.io.cfg.host):
            for f in Path('/tmp').glob('*.log'):
                os.rename(str(f), f'{self.io.cfg.host}_{self.io.cfg.log_dir}/{f}')
        else:
            subprocess.run(['scp', f'{host}:/tmp/*.log', str(local_log_dir)], check=True)
            subprocess.run(['scp', '-r', f'{host}:/tmp/bag', str(local_log_dir)], check=True)
            subprocess.run(['ssh', host, 'rm -f /tmp/*.log'], check=True)


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
