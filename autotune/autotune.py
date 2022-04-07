#!/usr/bin/python3

import titanlib
import random
from typing import Callable, Union, Tuple
import numpy as np
import sys
import math
import matplotlib.pyplot as plt

# from functools import reduce

# typedefs
numeric = Union[int, float]

# constants
m = 0.5


def gen_errors(
    values: np.ndarray, num_errors: int, gen_func: Callable[[], int]
) -> np.ndarray:
    assert num_errors <= len(values)
    error_indices = random.sample(
        range(len(values)), num_errors
    )  # FIXME: maybe we don't need the assert? I think this throws an exception in the same case

    errors = np.zeros(len(values))

    for i in error_indices:
        errors[i] = gen_func()

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


def temperature_errorfunc(error: int, value: float) -> float:
    if error != 0:
        return value + error
    return value


def plot_iso_performance_lines(ax, m):
    for i in [x / 10.0 for x in range(-math.ceil(m) * 10, 10, 1)]:
        ax.plot([0, 1], [i, m + i], linestyle="dashed", color="gray")
    return ax


def gen_error_temperature() -> int:
    return random.choice([-5, -3, -2, -1, 1, 2, 3, 5])


def make_h_far_plot(
    hit_rates: np.ndarray,
    false_alarm_rates: np.ndarray,
    thresholds: np.ndarray,
):
    fig, ax = plt.subplots()
    ax.plot(false_alarm_rates, hit_rates)

    for i in range(len(hit_rates)):
        ax.text(false_alarm_rates[i], hit_rates[i], str(thresholds[i]) + "σ")

    ax.plot([0, 1], [0, 1], linestyle="dotted", color="gray")
    ax = plot_iso_performance_lines(ax, m)

    plt.xlim(0, 1)
    plt.ylim(0, 1)

    ax.set_xlabel("False alarm rate")
    ax.set_ylabel("Hit rate")

    fig.show()
    fig.savefig("hfar.png", dpi=300)


def make_threshold_cost_plot(thresholds: np.ndarray, costs: np.ndarray):
    fig, ax = plt.subplots()
    ax.plot(thresholds, costs)

    ax.set_xlabel("Threshold (in standard deviations)")
    ax.set_ylabel("Cost")

    fig.show()
    fig.savefig("cost_threshold.png", dpi=300)


def main():
    # locations = titanlib.Points([60, 60.1, 60.2], [10, 10, 10], [0, 0, 0])
    # values = [0, 1, 1]
    locations, values = read_QCed_netatmo_data(sys.argv[1])

    errors = gen_errors(values, len(values) // 10, gen_error_temperature)
    seeded_values = seed_errors(values, errors, precipitation_errorfunc)

    # print("seeded_values: ", seeded_values)

    hit_rates = []
    false_alarm_rates = []
    costs = []
    thresholds = [x / 10.0 for x in range(5, 50, 5)]
    for threshold in thresholds:
        print("-- TESTING WITH threshold: ", threshold, " --")

        results = titanlib.buddy_check(
            locations,
            seeded_values,
            [10000],
            [3],
            threshold,
            200,
            0,
            1,
            3,
        )

        # print("results: ", results)
        # print("flag_count: ", reduce(lambda x, y: x + y, results))

        hit_rate, false_alarm_rate = calc_hit_FR_rates(results, errors)

        cost = cost_function(hit_rate, false_alarm_rate, m)

        hit_rates.append(hit_rate)
        false_alarm_rates.append(false_alarm_rate)
        costs.append(cost)

        print("hit_rate: ", hit_rate)
        print("false_alarm_rate: ", false_alarm_rate)
        print("cost: ", cost)

    make_h_far_plot(hit_rates, false_alarm_rates, thresholds)
    make_threshold_cost_plot(thresholds, costs)


if __name__ == "__main__":
    main()
