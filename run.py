import numpy as np
import time
import datetime

import app


def unixtime_to_str(unixtime):
    dt = datetime.datetime.utcfromtimestamp(int(unixtime))
    return "%04d-%02d-%02dT%02dZ" % (dt.year, dt.month, dt.day, dt.hour)

def variable_to_str(variable):
    if variable == "ta":
        return "Temperature"
    elif variable == "rr":
        return "Precipitation"
    else:
        raise NotImplementedError


try:
    if 1:
        import metio.titan
        datasets = list()
        settings = dict()
        # settings["winter_rr"] = [1582362000, 'rr']
        # settings["summer_rr"] = [1564876800, 'rr']
        # settings["winter_ta"] = [1580947200, 'ta']
        # settings["summer_ta"] = [1564833600, 'ta']
        settings["now"] = [1582786800, 'ta']
        s_time = time.time()

        for key in settings:
            dataset = metio.titan.get([settings[key][0]],settings[key][1], latrange=[59.3, 60.1], lonrange=[10, 11.5])
            # dataset = metio.titan.get([settings[key][0]],settings[key][1], dataset="thomasn")
            # dataset.filter(prids=range(0, 15), latrange=[59.3, 60.1], lonrange=[10, 11.5])
            if settings[key][1] == "rr":
                dataset.filter(prids=range(0, 15))
            name = "%s: %s" % (variable_to_str(settings[key][1]), unixtime_to_str(settings[key][0]))
            datasets += [{"name": name, "lats": dataset.lats, "lons": dataset.lons, "elevs": dataset.elevs, "values": dataset.values[0, :], "variable": settings[key][1]}]
        print("Time to load datasets: %.1fs" % (time.time() - s_time))
    else:
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
