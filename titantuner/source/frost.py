"""This module reads observations from frost"""


def get(frost_client_id: str, variable: str, unixtime: int) -> titantuner.Dataset:
    """Returns a dataset with observations for the given variable and time"""
    raise NotImplementedError()

def get_available_timeseries(frost_client_id: str, variable: str) -> list:
    """Returns a list of station IDs available for the given variable"""
    raise NotImplementedError()
