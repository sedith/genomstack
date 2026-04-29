from .base import Component


class Qualisys(Component):
    def setup(self) -> None:
        self.call('connect', self.component_cfg.host)

    ## empty log functions
    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass



class Optitrack(Component):
    def setup(self) -> None:
        self.call('connect', self.component_cfg.host, self.component_cfg.port)

    ## empty log functions
    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass
