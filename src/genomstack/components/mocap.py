from .base import Component


class Qualisys(Component):
    def setup(self) -> None:
        self.call('connect', self.component_cfg.host)

    def get_current_state(self) -> dict:
        return self.call('bodies', self.component_cfg.body)['bodies']

    def body_port(self) -> str:
        return f'{self.name}/bodies/{self.component_cfg.body}'

    ## empty log functions
    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass



class Optitrack(Component):
    def setup(self) -> None:
        self.call('connect', self.component_cfg.host, self.component_cfg.port)

    def get_current_state(self) -> dict:
        return self.call('bodies', self.component_cfg.body)['bodies']

    def body_port(self) -> str:
        return f'{self.name}/bodies/{self.component_cfg.body}'

    ## empty log functions
    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass
