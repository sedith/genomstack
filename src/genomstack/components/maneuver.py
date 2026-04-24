from .base import Component
from math import pi


class Maneuver(Component):
    NAME = 'maneuver'

    def setup(self) -> None:
        self.call('set_bounds', {
            'xmin': -10, 'xmax': 10,
            'ymin': -10, 'ymax': 10,
            'zmin': 0, 'zmax': 10,
            'yawmin': -2*pi, 'yawmax': 2*pi,
        })

        self.call('set_velocity_limit', {
            'v': self.cfg.maneuver.vmax,
            'w': self.cfg.maneuver.wmax,
        })

        self.call('set_acceleration_limit', {
            'a': self.cfg.maneuver.amax,
            'dw': self.cfg.maneuver.dwmax,
        })


        self.connect_port('state', 'pom/frame/robot')
