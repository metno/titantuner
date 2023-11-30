import numpy as np
import requests


import titantuner
from . import Source


"""This module reads observations from frost"""

class FrostSource(Source):
    def __init__(self, frost_client_id: str):
        self.frost_client_id = frost_client_id
        self.variables = [
                "air_temperature",
                "max(wind_speed PT1H)",
                "max(wind_speed_of_gust PT1H)",
                "sum(precipitation_amount PT1H)"
            ]

    @property
    def keys(self) -> list:
        return self.variables

    @property
    def key_label(self) -> str:
        return "Variable"

    @property
    def requires_time(self):
        return True

    def load(self, key: int, unixtime: int) -> titantuner.dataset.Dataset:
        """Returns a dataset with observations for the given variable and time"""
        variable = key
        host = "frost-beta.met.no"
        endpoint = "https://%s/api/v1/obs/met.no/filter/get?" % host
        start = unixtime_to_reference_time(unixtime)
        end = unixtime_to_reference_time(unixtime + 3600)
        parameters = dict()
        parameters["elementids"] = variable
        parameters["stationcountries"] = "Norge"
        parameters["stationalternateidkeys"] = "wmo"
        parameters["time"] = "%s/%s" % (start, end)
        parameters["timeresolutions"] = "PT1H"
        parameters["incobs"] = "true"
        timeout = 30

        r = requests.get(
            endpoint,
            parameters,
            auth=(self.frost_client_id, ""),
            timeout=timeout,
        )

        values, lats, lons, elevs, units = parse(r.json())
        name = "frost"
        dataset = titantuner.dataset.Dataset(name, lats, lons, elevs, values, unixtime, variable)
        return dataset

def unixtime_to_reference_time(unixtime):
    if unixtime == "now":
        return unixtime

    date, hour = titantuner.unixtime_to_date(unixtime)
    minutes = unixtime // 60 % 60
    seconds = unixtime % 60
    return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (
        date // 10000,
        date // 100 % 100,
        date % 100,
        hour,
        minutes,
        seconds,
    )


def parse(data):
    """Parse json output from frost (oda)"""
    values = list()
    lats = list()
    lons = list()
    elevs = list()
    units = None
    data = data["data"]["tseries"]
    metadata = dict()
    for tseries in data:
        id = "SN%d" % tseries["header"]["id"]["stationid"]
        units = tseries["header"]["extra"]["element"]["unit"]

        # Use this for kvkavka label, not for filter
        # typeid = tseries["header"]["id"]["stationidtype"]
        # if typeid != "nationalnummer":
        #     print("Skipping station %s, wrong StationIDType=%s" % (id, typeid))
        #     continue

        lat = float(tseries["header"]["extra"]["station"]["location"][0]["value"]["latitude"])
        lon = float(tseries["header"]["extra"]["station"]["location"][0]["value"]["longitude"])
        elev = 0

        # TODO: Check this output
        # https://frost-staging.met.no/api/v1/obs/met.no/kvkafka/get?stationids=18700&levels=0&sensors=0&elementids=air_temperature&time=latest&latestmaxage=PT1H&latestlimit=1&incobs=true
        # And parse the output properly

        # TODO:
        if len(tseries["observations"]) == 0:
            continue

        observations = tseries["observations"]
        for observation in observations:
            reference_time = observation["time"]
            date = int(reference_time[0:4] + reference_time[5:7] + reference_time[8:10])
            hour = int(reference_time[11:13])
            minute = int(reference_time[14:16])
            second = int(reference_time[17:19])
            # if minute == 0 and second == 0:

            value = observation["body"]["value"]

            if "kvcorrqc1" in observation["body"]:
                # Try to use kvalobs-corrected values if they exist
                value = observation["body"]["kvcorrqc1"]
            elif "kvcheckfailed" in observation["body"]:
                # Don't use this observation at all if the value is flagged
                continue

            if value in ["-32766", "-32767"]:
                # These are special codes with bizare meaning. Ask Ketil Tunheim:
                # ... there's -32766 and -32767, I don't remember what difference they are meant to
                # signify; but kvalobs writes them for timeseries where people's old scripts require
                # and demand that there always is a timestep (and it's a way to definitely know if a
                # value was missing unintentionally as opposed to intentionally because that station
                # doesn't measure at that time)
                continue

            unixtime = (
                titantuner.date_to_unixtime(date) + hour * 3600 + minute * 60 + second
            )
            if value == "":
                value = np.nan
            value = float(value)

            # TODO: Deal with special values, as with KDVH

            if not np.isnan(value):
                values += [value]
                lats += [lat]
                lons += [lon]
                elevs += [elev]
    return values, lats, lons, elevs, units
