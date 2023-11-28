import numpy as np
import sys
import os

import titantuner.app


def main():
    print(sys.argv)
    if len(sys.argv) == 2:
        datasets = list()
        dir = sys.argv[1]
        if os.path.exists(dir):
            pass
        else:
            print("Could not find data directory '%s'" % dir)
            sys.exit(1)
        filenames = os.listdir(dir)
        filenames.sort()
        if len(filenames) > 100:
            print("Too many data files (expect max 100 files)")
            sys.exit(1)
        for filename in filenames:
            filename = "%s/%s" % (dir, filename)
            if not os.path.isfile(filename):
                continue
            # lats, lons, elevs, values = read_titan(filename, latrange=[59.3, 60.1], lonrange=[10, 11.5])
            lats, lons, elevs, values = parse_titan_file(filename)
            print(filename)
            print(filename.find('_ta_'))
            if filename.find('_ta_') >= 0:
                variable = 'ta'
            else:
                variable = 'rr'
            print(variable)
            name = filename
            datasets += [{"name": name, "lats": lats, "lons": lons, "elevs": elevs, "values": values, "variable": variable}]
    else:
        ### Create your own data here
        N = 1000
        lats = np.random.randn(N) + 60
        lons = np.random.randn(N) + 10.7
        elevs = np.random.rand(N)*200
        values = np.random.randn(N) * 5 + 2
        variable = "ta"
        datasets = [{"name": "example", "lats": lats, "lons": lons, "elevs": elevs, "values": values, "variable": variable}]

    application = titantuner.app.App(datasets)


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


main()
