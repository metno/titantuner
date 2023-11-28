import os
import sys
import numpy as np


def load_default() -> list:
    """Loads data from the default data directory"""
    return load(get_default_data_dir())

def get_default_data_dir() -> str:
    curr_dir = os.path.dirname(__file__)
    return curr_dir + "/data"

def load(directory: str) -> list:
    """Loads data from a specified directory and returns a list of datasets"""
    datasets = list()
    if os.path.exists(directory):
        pass
    else:
        print("Could not find data directory '%s'" % directory)
        sys.exit(1)
    filenames = os.listdir(directory)
    filenames.sort()
    if len(filenames) > 100:
        print("Too many data files (expect max 100 files)")
        sys.exit(1)

    for filename in filenames:
        filename = "%s/%s" % (directory, filename)
        if not os.path.isfile(filename):
            continue
        # lats, lons, elevs, values = read_titan(filename, latrange=[59.3, 60.1], lonrange=[10, 11.5])
        lats, lons, elevs, values = parse_titan_file(filename)

        # Figure out what variable this dataset contains
        if filename.find('_ta_') >= 0:
            variable = 'ta'
        else:
            variable = 'rr'
        print(f"Opening {filename}. Variable {variable}.")
        name = os.path.basename(filename)
        datasets += [{"name": name, "lats": lats, "lons": lons, "elevs": elevs, "values": values, "variable": variable}]
    return datasets


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

