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

## Running titantuner on sample data

Some sample data from Norwegian Synop stations are provided in the data/ directory. To use these data, run 
the following command:

```bash
./serve data
```

## Running titantuner on your own data

Create files like the following (one file for each separate time and variable):

lon;lat;elev;value
9.4023;61.5308;928;3.1
10.6878;60.0513;360;2.6

lat and lon are in degrees, elev in meters, and value is the measurement.
