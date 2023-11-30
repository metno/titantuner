import os
import sys
import numpy as np


class Dataset:
    def __init__(self, name: str, lats: list, lons: list, elevs: list, values: list, unixtime: int, variable: str):
        self.name = name
        self.lats = lats
        self.lons = lons
        self.elevs = elevs
        self.values = values
        self.unixtime = unixtime
        self.variable = variable



