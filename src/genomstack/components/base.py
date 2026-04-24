from __future__ import annotations
from typing import Any


class Component:
    NAME: str | None = None

    def __init__(self, cfg: RobotConfig):
        if self.NAME is None:
            raise ValueError(f'{self.__class__.__name__}.NAME must be defined')

        self.cfg = cfg
        self.handle = None

    @property
    def name(self) -> str:
        return self.NAME

    def call(self, method: str, *args, **kwargs) -> Any:
        """Call a service/method on the underlying GenoM handle."""

        if not hasattr(self.handle, method):
            raise AttributeError(
                f'Component {self.NAME} has no method {method}'
            )

        fn = getattr(self.handle, method)
        return fn(*args, **kwargs)

    def connect_port(self, local: str, remote: str) -> None:
        """Connect a local GenoM port to a remote port."""
        return self.call('connect_port', {'local': local, 'remote': remote})

    def setup(self) -> None:
        """Connect external resources, apply configuration and wire ports."""
        raise NotImplementedError()

    def start_log(self) -> None:
        """Start component-specific logging."""
        self.call('log', f'/tmp/{self.NAME}.log')

    def stop_log(self) -> None:
        """Stop component-specific logging."""
        self.call('log_stop')
