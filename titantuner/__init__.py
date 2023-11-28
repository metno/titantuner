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

def main():
    import titantuner.__main__
    titantuner.__main__.main()

