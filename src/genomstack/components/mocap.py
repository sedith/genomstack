from .base import Component


class Qualisys(Component):
    NAME = 'qualisys'

    def setup(self) -> None:
        self.call('connect', self.cfg.mocap.host)

    def get_current_state(self) -> dict:
        return self.call('bodies', self.cfg.mocap.body)['bodies']

    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass



class Optitrack(Component):
    NAME = 'optitrack'

    def setup(self) -> None:
        self.call('connect', self.cfg.mocap.host, self.cfg.mocap.port)

    def get_current_state(self):
        return self.call('bodies', self.cfg.mocap.body)['bodies']

    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass
