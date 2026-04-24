from .base import Component
import json


class Rotorcraft(Component):
    NAME = 'rotorcraft'

    def setup(self) -> None:
        self.call('connect', {
            'serial': self.cfg.rotorcraft.serial,
            'baud': 0,
        })

        self.call('set_sensor_rate', {
            'rate': {'imu': 1000, 'mag': 0, 'motor': 20, 'battery': 1}
        })
        self.call('set_imu_filter', {
            'gfc': [20, 20, 20],
            'afc': [5, 5, 5],
            'mfc': [20, 20, 20],
        })

        if self.cfg.rotorcraft.calib:
            calib = json.load(open(self.cfg.rotorcraft.calib))
            self.call('set_imu_calibration', calib)

        self.connect_port('rotor_input', 'uavatt/rotor_input')

        self.call('stop')
