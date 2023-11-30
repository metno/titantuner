import calendar
import datetime
import numbers
import os
import pkgutil
import sys
import numpy as np


VERSION = "0.1.1"

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if module_name != "__main__":
        __all__.append(module_name)
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module


def date_to_unixtime(date, hour=0, min=0, sec=0):
    """Convert YYYYMMDD(HHMMSS) to unixtime

    Arguments:
       date (int): YYYYMMDD
       hour (int): HH
        min (int): MM
        sec (int): SS

    Returns:
       int: unixtime [s]
    """
    if not isinstance(date, int):
        raise ValueError("Date must be an integer")
    if not isinstance(hour, numbers.Number):
        raise ValueError("Hour must be a number")
    if hour < 0 or hour >= 24:
        raise ValueError("Hour must be between 0 and 24")
    if min < 0 or hour >= 60:
        raise ValueError("Minute must be between 0 and 60")
    if sec < 0 or hour >= 60:
        raise ValueError("Second must be between 0 and 60")

    year = date // 10000
    month = date // 100 % 100
    day = date % 100
    ut = calendar.timegm(datetime.datetime(year, month, day).timetuple())
    return ut + (hour * 3600) + (min * 60) + sec


def unixtime_to_date(unixtime):
    """Convert unixtime to YYYYMMDD

    Arguments:
       unixtime (int): unixtime [s]

    Returns:
       int: date in YYYYMMDD
       int: hour in HH
    """
    if not isinstance(unixtime, numbers.Number):
        raise ValueError("unixtime must be a number")

    dt = datetime.datetime.utcfromtimestamp(int(unixtime))
    date = dt.year * 10000 + dt.month * 100 + dt.day
    hour = dt.hour
    return date, hour


def main():
    import titantuner.__main__
    titantuner.__main__.main()
