from .base import Component


class Pom(Component):
    def setup(self) -> None:
        self.call('set_prediction_model', {
            'pmodel': '::pom::constant_acceleration'
        })
        self.call('set_process_noise', {
            'max_jerk': 100, 'max_dw': 50
        })
        self.call('set_history_length', {
            'history_length': 0.25
        })

        self.connect_port('measure/imu', 'rotorcraft/imu')
        self.call('add_measurement', 'imu')

        self.connect_port('measure/mocap', f'{self.robot.mocap.component_cfg.type}/bodies/{self.robot.mocap.component_cfg.body}')
        self.call('add_measurement', 'mocap')

    def start_log(self) -> None:
        self.call('log_state', f'/tmp/{self.name}.log')
        self.call('log_measurements',  f'/tmp/{self.name}-measurements.log')

    def get_current_state(self) -> dict:
        return self.call('frame', 'robot')['frame']
