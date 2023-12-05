import os
import sys
import numpy as np

import titantuner
from . import Source


"""This class load data from standardized Titan output files"""
class TitanSource(Source):
    def __init__(self, directory):
        if not os.path.exists(directory):
            print("Could not find data directory '%s'" % directory)
            raise ValueError()
        filenames = os.listdir(directory)
        filenames.sort()
        self.filenames = filenames
        self.names = dict()
        for filename in self.filenames:
            self.names[filename] = f"{directory}/{filename}"

    @property
    def keys(self) -> list:
        return list(self.names.keys())

    @property
    def key_label(self) -> str:
        return "Dataset"

    def load(self, key: str) -> titantuner.dataset.Dataset:
        filename = self.names[key]
        lats, lons, elevs, values, qc_dico = parse_titan_file(filename, qc=True)

        # Figure out what variable this dataset contains
        if filename.find('_ta_') >= 0:
            variable = 'ta'
        else:
            variable = 'rr'
        print(f"Opening {filename}. Variable {variable}.")
        name = os.path.basename(filename)
        dataset = titantuner.dataset.Dataset(name, lats, lons, elevs, values, None, 
                                             variable, qc_dico)
        return dataset

def parse_titan_file(filename, latrange=None, lonrange=None, qc=False):
    """ Parses files produced by titan.R """
    data = dict()
    lats = list()
    lons = list()
    elevs = list()
    values = list()
    if qc:
        qc_dico = {}
    with open(filename, 'r') as file:
        header = file.readline().strip().split(';')
        Ilat = header.index('lat')
        Ilon = header.index('lon')
        Ielev = header.index('elev')
        # look for eventual qc columns, allows several flag columns
        if qc:
            Iqcs = [i for i, s in enumerate(header) if "qc" in s]
            qc_column_names = [header[index] for index in Iqcs]
            for qc_column_name in qc_column_names:
                qc_dico[qc_column_name] = list()
        if 'prid' in header:
            Iprovider = header.index('prid')
        else:
            Iprovider = None
        Ivalue = header.index('value')
        for line in file:
            words = line.strip().split(';')
            try:
                lat = float(words[Ilat])
                if latrange is not None and (lat < latrange[0] or lat > latrange[1]):
                    continue
                lon = float(words[Ilon])
                if lonrange is not None and (lon < lonrange[0] or lon > lonrange[1]):
                    continue
                elev = -999
                if words[Ielev] != "NA":
                    elev = float(words[Ielev])
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
                if qc:
                    for idx, qc_column_name in zip(Iqcs, qc_column_names):
                        qcflag = -999
                        if words[idx] != "NA":
                            qcflag = float(words[idx])
                        qc_dico[qc_column_name] += [qcflag]
            except (ValueError, IndexError) as e:
                print(e)
    if qc:
        return np.array(lats), np.array(lons), np.array(elevs), np.array(values), qc_dico
    else:
        return np.array(lats), np.array(lons), np.array(elevs), np.array(values)

def get_default_data_dir() -> str:
    curr_dir = os.path.dirname(__file__)
    return curr_dir + "/data"

