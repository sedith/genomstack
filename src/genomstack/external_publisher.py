from __future__ import annotations


class ExternalPublisher:
    def __init__(self, cfg: Config, name: str, robot: Robot):
        self.cfg = cfg
        self.name = name
        self.robot = robot
        self.publisher = None

    @property
    def publisher_cfg(self) -> Config:
        return self.cfg.external_publishers[self.name]

    @property
    def target(self) -> Component:
        return getattr(self.robot, self.publisher_cfg.target)

    def setup(self) -> None:
        make_publisher = getattr(self.target.handle, self.publisher_cfg.publisher)
        self.publisher = make_publisher(self.publisher_cfg.path)
        self.target.connect_port(
            self.publisher_cfg.port,
            self.publisher_cfg.path,
        )

    def publish(self, msg: dict) -> None:
        self.publisher(msg)

    ## empty log functions
    def start_log(self) -> None:
        pass

    def stop_log(self) -> None:
        pass
