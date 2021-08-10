# Titantuner
The titantuner is a web interface for tuning the many parameters of quality control methods in [titanlib](https://github.com/metno/titanlib).

![Example of titantuner](extras/image.jpg)

## Installation

```bash
pip3 install -r requirements.txt
```

## Running titantuner on synthetic data

```bash
./serve data
```
This starts a webserver locally on your computer, making the titantuner available in the browser.

## Running titantuner on sample data

Some sample data from Norwegian Synop stations are provided in the data/ directory. To use these data, run 
the following command:

```bash
./serve data
```

## Running titantuner on your own data

Titantuner can parse data files organzed as follows:

```
lon;lat;elev;value
9.4023;61.5308;928;3.1
10.6878;60.0513;360;2.6
```

where lat and lon are in degrees, elev in meters, and value is the measurement. Each row represents one observation, and each file represents observations for one time.
