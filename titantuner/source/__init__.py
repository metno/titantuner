import os
import pkgutil


import titantuner

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if module_name != "__main__":
        __all__.append(module_name)
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module

def load_default() -> list:
    """Loads data from the default data directory"""
    return titantuner.source.titan_output.load(get_default_data_dir())

def get_default_data_dir() -> str:
    curr_dir = os.path.dirname(__file__)
    return curr_dir + "/data"
