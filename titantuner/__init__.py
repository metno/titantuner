import os
import pkgutil
import sys
import numpy as np


VERSION = "0.1.1"
__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if module_name != "__main__":
        __all__.append(module_name)
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module

class Dataset:
    def __init__(self, name: str, lats: list, lons: list, elevs: list, values: list, unixtime: int, variable: str):
        self.name = name
        self.lats = lats
        self.lons = lons
        self.elevs = elevs
        self.values = values
        self.unixtime = unixtime
        self.variable = variable

def main():
    import titantuner.__main__
    titantuner.__main__.main()
