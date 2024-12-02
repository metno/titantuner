import os
import sys
import numpy as np
import glob

import titantuner
from . import Source


"""This class load data from standardized Titan output files"""
class TitanSource(Source):
    def __init__(self, directories_or_patterns: list):
        if not isinstance(directories_or_patterns, list):
            raise ValueError("directories_or_patterns must be a list")
        filenames = self.get_filenames(directories_or_patterns)

        self.names = dict()
        for filename in filenames:
            if not os.path.isdir(filename):
                name = os.path.basename(filename)
                self.names[name] = filename

    @staticmethod
    def get_filenames(directories_or_patterns: list):
        """Returns all filenames in the list of directories or file patterns"""

        if not isinstance(directories_or_patterns, list):
            raise ValueError("directories_or_patterns must be a list")
        filenames = list()
        for directory in directories_or_patterns:
            if os.path.isdir(directory):
                directory = directory.rstrip('/') # Prevent double slahses (makes unit testing easier)
                filenames += [f"{directory}/{d}" for d in os.listdir(directory)]
            else:
                filenames += glob.glob(directory)

            filenames.sort()
        return filenames

    @property
    def keys(self) -> list:
        return list(self.names.keys())

    @property
    def key_label(self) -> str:
        return "Dataset"

    def load(self, key: str) -> titantuner.dataset.Dataset:
        filename = self.names[key]
        try:
            lats, lons, elevs, values = self.parse_titan_file(filename)
        except Exception as e:
            # TODO: I wanted to remove  the invalid keys from the list but somehow if I do
            # self.names.pop(key)
            # then I have issues in case of having only 1 other valid file, for some reason the valid name cannot be selectd one
            # (if more than 1 valid name, it seems to behave ok otherwise)
            raise titantuner.InvalidDatasetException(filename)
        # Figure out what variable this dataset contains
        if filename.find('_ta_') >= 0:
            variable = 'ta'
        else:
            variable = 'rr'
        print(f"Opening {filename}. Variable {variable}.")
        name = os.path.basename(filename)
        dataset = titantuner.dataset.Dataset(name, lats, lons, elevs, values, None, variable)
        return dataset

    @staticmethod
    def parse_titan_file(filename, latrange=None, lonrange=None):
        """ Parses files produced by titan.R """
        data = dict()
        lats = list()
        lons = list()
        elevs = list()
        values = list()
        with open(filename, 'r') as file:
            header = file.readline().strip().split(';')
            Ilat = header.index('lat')
            Ilon = header.index('lon')
            Ielev = header.index('elev')
            if 'prid' in header:
                Iprovider = header.index('prid')
            else:
                Iprovider = None
            Ivalue = header.index('value')
            for line in file:
                words = line.strip().split(';')
                lat = float(words[Ilat])
                if latrange is not None and (lat < latrange[0] or lat > latrange[1]):
                    continue
                lon = float(words[Ilon])
                if lonrange is not None and (lon < lonrange[0] or lon > lonrange[1]):
                    continue
                elev = -999
                if words[Ielev] != "NA":
                    elev = float(words[Ielev])
                try:
                    value = float(words[Ivalue])
                    """
                    if Iprovider is not None:
                        provider = int(words[Iprovider])
                        if provider > 20:
                            continue
                    """
                    lats += [lat]
                    lons += [lon]
                    elevs += [elev]
                    values += [value]
                except Exception as e:
                    print(e)
        return np.array(lats), np.array(lons), np.array(elevs), np.array(values)

    @staticmethod
    def get_default_data_dir() -> str:
        curr_dir = os.path.dirname(__file__)
        return curr_dir + "/data"

