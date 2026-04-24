from .config import Config
from .components import Component
import genomix


class Runtime:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.g = None
        self._handles = {}

    def connect(self):
        self.g = genomix.connect(self.cfg.host)
        self.g.rpath(self.cfg.plugin_path)

    def load(self, component: Component):
        if component.name not in self._handles:
            self._handles[component.name] = self.g.load(component.name)
            component.handle = self._handles[component.name]
        return self._handles[component.name]
