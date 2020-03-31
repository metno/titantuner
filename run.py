import numpy as np
import time
import datetime
import sys
import os

import app


def unixtime_to_str(date, hour):
    year = date // 10000
    month = date // 100 % 100
    day = date % 100
    return "%04d-%02d-%02dT%02dZ" % (year, month, day, hour)

def variable_to_str(variable):
    if variable == "ta":
        return "Temperature"
    elif variable == "rr":
        return "Precipitation"
    else:
        raise NotImplementedError


def read_titan(filename, latrange=None, lonrange=None):
    data = dict()
    lats = list()
    lons = list()
    elevs = list()
    values = list()
    with open(filename, 'r') as file:
        header = file.readline().split(';')
        Ilat = header.index('lat')
        Ilon = header.index('lon')
        Ielev = header.index('elev')
        Iprovider = header.index('prid')
        Iflag = header.index('dqc')
        Ivalue = header.index('value')
        for line in file:
            words = line.split(';')
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
                flag = float(words[Iflag])
                provider = int(words[Iprovider])
                if provider < 20:
                    continue
                lats += [lat]
                lons += [lon]
                elevs += [elev]
                values += [value]
            except Exception as e:
                print(e)
    return lats, lons, elevs, values


def get_titan_filename(date, hour, variable, dataset='best'):
    """
        Returns None if no file available
    """
    year = date / 10000
    month = date / 100 % 100
    day = date % 100
    if dataset == 'best':
        filename = "/lustre/storeB/immutable/archive/projects/metproduction/yr_short/%d/%02d/%02d/obs_%s_%dT%02dZ.txt" % (year, month, day, variable, date, hour)
        if not os.path.exists(filename):
            filename = "/lustre/storeB/project/metkl/klinogrid/archive/met_nordic_analysis/v1_work/obs//%d/%02d/%02d/obs_%s_%dT%02dZ.txt" % (year, month, day, variable, date, hour)
    elif dataset == 'v1':
        filename = "/lustre/storeB/project/metkl/klinogrid/archive/met_nordic_analysis/v1_work/obs_%s/%d/%02d/%02d/obs_%s_%dT%02dZ.txt" % (variable, year, month, day, variable, date, hour)
    elif dataset == 'operational':
        filename = "/lustre/storeB/immutable/archive/projects/metproduction/yr_short/%d/%02d/%02d/obs_%s_%dT%02dZ.txt" % (year, month, day, variable, date, hour)
    if not os.path.exists(filename):
        return None
    return filename


def unixtime_to_date(unixtime):
    """ Convert unixtime to YYYYMMDD

    Arguments:
       unixtime (int): unixtime

    Returns:
       int: date in YYYYMMDD
    """
    dt = datetime.datetime.utcfromtimestamp(int(unixtime))
    date = dt.year * 10000 + dt.month * 100 + dt.day
    return date


try:
    try:
        datasets = list()
        settings = dict()
        # settings["winter_rr"] = [1582362000, 'rr']
        # settings["summer_rr"] = [1564876800, 'rr']
        # settings["winter_ta"] = [1580947200, 'ta']
        # settings["summer_ta"] = [1564833600, 'ta']
        curr_time = (time.time() // 3600 - 1)* 3600
        settings["now"] = [unixtime_to_date(curr_time), (int(curr_time) % 3600) // 3600, 'ta']
        s_time = time.time()

        for key in settings:
            print(settings[key])
            filename = get_titan_filename(settings[key][0], settings[key][1], settings[key][2])
            if os.path.exists(filename):
                print(filename)
                lats, lons, elevs, values = read_titan(filename, latrange=[59.3, 60.1], lonrange=[10, 11.5])
                name = "%s: %s" % (variable_to_str(settings[key][2]), unixtime_to_str(settings[key][0], settings[key][1]))
                datasets += [{"name": name, "lats": lats, "lons": lons, "elevs": elevs, "values": values, "variable": settings[key][2]}]
            else:
                print("Could not load %s" % filename)
        print("Time to load datasets: %.1fs" % (time.time() - s_time))
    except Exception as e:
        print("Could not load metio. %s" % e)
        ### Create your own data here
        N = 1000
        lats = np.random.randn(N) + 60
        lons = np.random.randn(N) + 10.7
        elevs = np.random.rand(N)*200
        values = np.random.randn(N) * 5 + 2
        variable = "ta"
        datasets = [{"name": "example", "lats": lats, "lons": lons, "elevs": elevs, "values": values, "variable": variable}]

    application = app.App(datasets)
except Exception as e:
    print(e)


#main()
