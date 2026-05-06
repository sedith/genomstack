import re
import socket

from .config import Config
from .components import Component
import genomix

_CONNECT_TIMEOUT = 5  # seconds


class Runtime:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.g = None
        self._handles = {}

    def connect(self) -> None:
        # Fast reachability check so we fail with a clear message instead of
        # hanging indefinitely when the remote genomixd is unreachable.
        addr = re.split(r':([^]:]+)$', self.cfg.host)
        host = addr[0]
        port = int(addr[1]) if len(addr) > 1 else 8080
        try:
            with socket.create_connection((host, port), timeout=_CONNECT_TIMEOUT):
                pass
        except OSError as e:
            raise ConnectionError(
                f'Cannot reach genomixd at {host}:{port} '
                f'(timeout={_CONNECT_TIMEOUT}s): {e}'
            ) from e

        self.g = genomix.connect(self.cfg.host)
        self.g.rpath(self.cfg.plugin_path)

    def load(self, component: Component) -> None:
        if component.name not in self._handles:
            if component.use_instance():
                self._handles[component.name] = self.g.load(component.gtype, '-i', component.name)
            else:
                self._handles[component.name] = self.g.load(component.gtype)

            component.handle = self._handles[component.name]
