import os
import sys
import numpy as np


class Dataset:
    def __init__(self, name: str, lats: list, lons: list, elevs: list, values: list, unixtime: int, variable: str, qc_dico):
        self.name = name
        self.lats = np.array(lats)
        self.lons = np.array(lons)
        self.elevs = np.array(elevs)
        self.values = np.array(values)
        self.unixtime = unixtime
        self.variable = variable
        self.qc_dico = qc_dico



