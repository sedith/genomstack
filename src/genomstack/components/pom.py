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

        if self.component_cfg.use_lidar:
            pub = self.call('measure', '/tmp/rko_lio')
            # pub({
            #     'measure': {'ts': {'sec': 0, 'nsec': 0}, 'intrinsic': 0,
            #     'pos': None, 'att': None, 'vel': None, 'avel': None, 'acc': None, 'aacc': None,
            #     'pos_cov': None, 'att_cov': None, 'att_pos_cov': None, 'vel_cov': None, 'avel_cov': None, 'acc_cov': None, 'aacc_cov': None}
            # })
            self.connect_port('measure/lidar', '/tmp/rko_lio')
            self.call('add_measurement', 'lidar')
        else:
            self.connect_port('measure/mocap', self.robot.mocap.body_port())
            self.call('add_measurement', 'mocap')

    def start_log(self) -> None:
        self.call('log_state', f'/tmp/{self.name}.log')
        self.call('log_measurements',  f'/tmp/{self.name}-measurements.log')

    def get_current_state(self) -> dict:
        return self.call('frame', 'robot')['frame']
