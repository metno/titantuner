import os
import pkgutil


import titantuner

class Source:
    @property
    def requires_time(self):
        return False

    @property
    def keys(self) -> int:
        raise NotImplementedError()

    @property
    def key_label(self) -> str:
        raise NotImplementedError()

    def load_index(self, index: int) -> titantuner.dataset.Dataset:
        raise NotImplementedError()

from .titan import *
from .frost import *
