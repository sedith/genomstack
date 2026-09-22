import numpy as np
from .robot_io import RobotIO
from .utils import quat2yaw


class Mission:
    def __init__(self, io: RobotIO, relative: bool = False):
        self.io = io
        self.relative = relative

        if self.relative:
            self.set_origin()

    ## transform helpers
    def set_origin(self) -> None:
        ## capture the current position and yaw as the relative origin
        frame = self.io.read('pom', 'frame/robot')['frame']
        pos = frame['pos']
        att = frame['att']
        self.p0 = np.array([pos['x'], pos['y'], pos['z']], dtype=float)
        self.yaw0 = quat2yaw([att['qw'], att['qx'], att['qy'], att['qz']])
        print(f'origin set: {self.p0[0]:.3f} {self.p0[1]:.3f} {self.p0[2]:.3f} [m],  yaw {self.yaw0:.3f} [rad]')

    def transform_pose(self, x, y, z, yaw):
        if not self.relative:
            return x, y, z, yaw

        ## rotate and translate the local command into the world frame
        c = np.cos(self.yaw0)
        s = np.sin(self.yaw0)
        p = self.p0 + np.array([c * x - s * y, s * x + c * y, z])
        return (*p, self.yaw0 + yaw)

    ## mission helpers
    def spin(self) -> None:
        print(f'- start spinning and logging')
        self.io.components['rotorcraft'].call('start')

    def start(self, z_start=0.25, ramp_duration=5, prompt=False) -> None:
        _, _, z_start, _ = self.transform_pose(0, 0, z_start, 0)
        print(f'- start: {z_start:.3f} [m] -- duration: {ramp_duration} [s]')
        if prompt:
            input('  | press enter ...')
        self.io.start_components()
        self.io.components['maneuver'].call('take_off', z_start, ramp_duration, ack=True)

    def goto(self, x, y, z, yaw, duration=0, prompt=False) -> None:
        x, y, z, yaw = self.transform_pose(x, y, z, yaw)
        print(f'- goto: {x:.3f} {y:.3f} {z:.3f} [m] -- {yaw:.3f} [rad] -- duration {duration}s')
        if prompt:
            input('  | press enter ...')
        self.io.components['maneuver'].call('goto', x, y, z, yaw, duration, ack=True)

    def gotoz(self, z=0.2, duration=0, prompt=False) -> None:
        _, _, z, _ = self.transform_pose(0, 0, z, 0)
        print(f'- goto z: {z:.3f} [m] -- duration: {duration} [s]')
        if prompt:
            input('  | press enter ...')
        self.io.components['maneuver'].call('take_off', z, duration, ack=True)

    def stop(self, prompt=False) -> None:
        print('- stop')
        if prompt:
            input('  | press enter ...')
        self.io.stop_logs()
        self.io.components['rotorcraft'].call('stop')
        self.io.export_logs()
