#!/usr/bin/python3

import titanlib
import random
from typing import Callable, Union, Tuple
import numpy as np
import sys

# from functools import reduce

# typedefs
numeric = Union[int, float]

# constants
m = 0.5


def gen_errors(values: np.ndarray, num_errors: int) -> np.ndarray:
    assert num_errors <= len(values)
    error_indices = random.sample(
        range(len(values)), num_errors
    )  # FIXME: maybe we don't need the assert? I think this throws an exception in the same case

    errors = np.zeros(len(values))

    for i in error_indices:
        errors[i] = 1

    return errors


def seed_errors(
    values: np.ndarray,
    errors: np.ndarray,
    errorfunc: Callable[[int, numeric], numeric],
) -> np.ndarray:
    for i in range(len(values)):
        if errors[i] != 0:
            values[i] = errorfunc(errors[i], values[i])

    return values  # TODO test whether numpy modifies in place


def calc_hit_FR_rates(results: np.ndarray, errors: np.ndarray) -> Tuple[float, float]:
    hits = 0
    FAs = 0

    perturbed = 0
    unperturbed = 0

    for i in range(len(results)):
        if errors[i] == 0:
            unperturbed += 1
            if results[i] != 0:
                FAs += 1

        if errors[i] != 0:
            perturbed += 1
            if results[i] != 0:
                hits += 1

    # defaults in case of divide by zero
    hit_rate = 1
    false_alarm_rate = 0

    if perturbed != 0:
        hit_rate = hits / perturbed
    if unperturbed != 0:
        false_alarm_rate = FAs / unperturbed

    return hit_rate, false_alarm_rate


def cost_function(hit_rate: float, false_alarm_rate: float, m: float) -> float:
    return 1 - hit_rate + (m * false_alarm_rate)


def read_QCed_netatmo_data(filename: str) -> Tuple[titanlib.Points, np.ndarray]:
    lats = []
    lons = []
    elevs = []
    values = []

    with open(filename) as f:
        next(f)  # skip first line (titles)
        for line in f:
            fields = line.split(";")

            prid = int(fields[4])
            qcflag = int(fields[5])
            if prid == 3 and qcflag == 0:
                lats.append(float(fields[0]))
                lons.append(float(fields[1]))
                elevs.append(float(fields[2]))
                values.append(float(fields[3]))

    return titanlib.Points(lats, lons, elevs), values


def precipitation_errorfunc(error: int, value: float) -> float:
    if error != 0:
        if value != 0:
            return 0
        else:
            return 1
    return value


def main():
    # locations = titanlib.Points([60, 60.1, 60.2], [10, 10, 10], [0, 0, 0])
    # values = [0, 1, 1]
    locations, values = read_QCed_netatmo_data(sys.argv[1])

    errors = gen_errors(values, len(values) // 10)
    seeded_values = seed_errors(values, errors, precipitation_errorfunc)

    # print("seeded_values: ", seeded_values)

    results = titanlib.buddy_check(
        locations,
        seeded_values,
        [5000],
        [2],
        0.5,
        200,
        0,
        1,
        2,
    )

    # print("results: ", results)
    # print("flag_count: ", reduce(lambda x, y: x + y, results))

    hit_rate, false_alarm_rate = calc_hit_FR_rates(results, errors)

    cost = cost_function(hit_rate, false_alarm_rate, m)

    print("hit_rate: ", hit_rate)
    print("false_alarm_rate: ", false_alarm_rate)
    print("cost: ", cost)


if __name__ == "__main__":
    main()
