import genomix
from .components import Component
from .config import Config
from .process import host_path


class Genomix:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.g = None
        self._handles = {}

    def connect(self) -> None:
        ## connect to the configured host and register its plugin path
        self.g = genomix.connect(self.cfg.host)
        for rpath in self.cfg.plugin_paths:
            self.g.rpath(host_path(rpath, self.cfg.host))

    def load(self, component: Component) -> None:
        if component.name not in self._handles:
            ## load either a named component instance or the default instance
            if component.use_instance():
                self._handles[component.name] = self.g.load(component.gtype, '-i', component.name)
            else:
                self._handles[component.name] = self.g.load(component.gtype)

            component.handle = self._handles[component.name]
