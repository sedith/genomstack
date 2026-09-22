from .base import Component
from math import pi


class Maneuver(Component):
    START_ORDER = 20

    def setup(self) -> None:
        self.call(
            'set_bounds',
            {
                'xmin': -500,
                'xmax': 500,
                'ymin': -500,
                'ymax': 500,
                'zmin': -500,
                'zmax': 500,
                'yawmin': -6 * pi,
                'yawmax': 6 * pi,
            },
        )

        self.call('set_velocity_limit', {'v': self.component_cfg.vmax, 'w': self.component_cfg.wmax})
        self.call('set_acceleration_limit', {'a': self.component_cfg.amax, 'dw': self.component_cfg.dwmax})

        self.connect_port('state', 'pom/frame/robot')

    def start(self) -> None:
        self.call('set_current_state')
