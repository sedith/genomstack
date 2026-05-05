import time
from genomix.event import GenoMError
from .base import Component

_PORT_RETRY_INTERVAL = 0.5  # seconds between retries
_PORT_RETRY_TIMEOUT = 10.0  # seconds before giving up


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

        for meas in self.component_cfg.meas:
            self._connect_port_with_retry(f'measure/{meas.name}', meas.port)
            self.call('add_measurement', meas.name, *meas.offset if 'offset' in meas else [])

    def _connect_port_with_retry(self, local: str, remote: str) -> None:
        deadline = time.monotonic() + _PORT_RETRY_TIMEOUT
        while True:
            try:
                self.connect_port(local, remote)
                return
            except GenoMError as e:
                if 'no_such_outport' not in str(e) or time.monotonic() >= deadline:
                    raise
                print(f'{self.name}: port {remote!r} not ready, retrying...')
                time.sleep(_PORT_RETRY_INTERVAL)

    def start_log(self) -> None:
        self.call('log_state', f'/tmp/{self.name}.log')
        self.call('log_measurements',  f'/tmp/{self.name}-measurements.log')
