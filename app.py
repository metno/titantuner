import titanlib
import numpy as np
import bokeh.plotting
import time
import math
import copy

from bokeh.io import output_file, show
from bokeh.layouts import column, row, widgetbox, gridplot
from bokeh.models import Button, Title, Text, Label, Panel, ColumnDataSource, GMapOptions
from bokeh.models.widgets import RangeSlider, Slider, PreText, Paragraph, TextInput, Select, RadioButtonGroup, CheckboxButtonGroup, Dropdown
from bokeh.models.widgets.widget import Widget
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc, show, output_file
from bokeh.tile_providers import get_provider, Vendors


class App(object):
    def __init__(self):
        self.ui = None

    def set_ui(self, value):
        self.ui_name = value
        ui = dict()
        # dropdown = Dropdown(label="Choose test", button_type="warning", menu=[("Sct", "sct"), ("Isolation", "isolation")])

        #dropdown = RadioButtonGroup(labels=[dataset["name"] for dataset in self.datasets], active=self.dataset_index)
        dropdown = Select(title="Dataset", options=[(i, dataset["name"]) for i, dataset in
            enumerate(self.datasets)], value=str(self.dataset_index))
        dropdown.on_change("value", self.choose_dataset_handler)
        ui["dataset"] = dropdown

        dropdown = RadioButtonGroup(labels=["SCT", "Isolation", "Buddy", "Buddy event"], active=self.uiname2id(value))
        dropdown.on_click(self.choose_test_handler)
        ui["type"] = dropdown

        ui["frac"] = Slider(start=0, end=100, value=100, step=10, title="Fraction of stations to use [%]")
        latrange = [np.floor(np.min(self.lats)), np.ceil(np.max(self.lats))]
        lonrange = [np.floor(np.min(self.lons)), np.ceil(np.max(self.lons))]
        ui["latrange"] = RangeSlider(start=latrange[0], end=latrange[1], value=latrange, step=0.1, title="Latitude range")
        ui["lonrange"] = RangeSlider(start=lonrange[0], end=lonrange[1], value=lonrange, step=0.1, title="Longitude range")
        if value == "sct":
            ui["nmin"] = Slider(start=50, end=1000, value=100, step=50, title="Minimum obs in box")
            ui["nmax"] = Slider(start=100, end=3000, value=300, step=100, title="Maximum obs in box")
            ui["nminprof"] = Slider(start=50, end=1000, value=100, step=50, title="Minimum obs to fit profile")
            ui["t2pos"] = Slider(start=0, end=10, value=4, step=0.1, title="T2pos [%s]" % self.units)
            ui["t2neg"] = Slider(start=0, end=10, value=4, step=0.1, title="T2neg [%s]" % self.units)
            ui["eps2"] = Slider(start=0, end=2, value=0.5, step=0.1, title="eps2 [%s**2]" % self.units)
            ui["dzmin"] = Slider(start=0, end=200, value=30, step=10, title="Min elev range to fit profile [m]")
            ui["dhmin"] = Slider(start=0, end=20000, value=10000, step=1000, title="Min horiz OI distance [m]")
            ui["dz"] = Slider(start=100, end=1000, value=200, step=100, title="Vertiacal OI distance [m]")
            ui["labels"] = CheckboxButtonGroup(labels=["Obs", "SCT", "Elev"], active=[0])

            #self.r4 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="red")
            #self.r3 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="navy")

        elif value == "isolation":
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Number of observations")
            ui["radius"] = Slider(start=1, end=50, value=15, step=1, title="Radius [km]")
        elif value == "buddy":
            ui["distance"] = Slider(start=1000, end=20000, value=5000, step=1000, title="Distance limit [m]")
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Minimum obs required")
            ui["threshold"] = Slider(start=0.1, end=5, value=2, step=0.1, title="Threshold")
            ui["elev_range"] = Slider(start=100, end=1000, value=300, step=100, title="Maximum elevation difference [m]")
            ui["elev_gradient"] = Slider(start=-5, end=10, value=6.5, step=0.5, title="Elevation gradient [%s/km]" % self.units)
            ui["min_std"] = Slider(start=0.1, end=5, value=1, step=0.1, title="Minimum neighbourhood std [%s]" % self.units)
            ui["num_iterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
        elif value == "buddy_event":
            ui["distance"] = Slider(start=1000, end=10000, value=5000, step=1000, title="Distance limit [m]")
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Minimum obs required")
            ui["threshold"] = Slider(start=0.05, end=5, value=0.1, step=0.05, title="Threshold")
            ui["elev_range"] = Slider(start=100, end=1000, value=300, step=100, title="Maximum elevation difference [m]")
            ui["elev_gradient"] = Slider(start=-5, end=10, value=0, step=0.5, title="Elevation gradient [%s/km]" % self.units)
            ui["event_threshold"] = Slider(start=0, end=5, value=0.2, step=0.1, title="Event threshold")
        ui["time"] = TextInput(value="None", title="Titanlib request time [s]")
        ui["stations"] = TextInput(value="None", title="Stations (removed [%])")
        ui["mean"] = TextInput(value="None", title="Average observed [%s]" % self.units)
        button = Button(background="orange", label="Update")
        button.on_click(self.button_click_callback)
        ui["button"] = button

        #ph = figure(title="Histogram") # , plot_height=800, plot_width=1200)
        #ui["histogram"] = ph
        self.edges = range(-20, 21)

        #self.r4 = ph.circle([], [], fill_color="gray", legend="OK", size=3)
        #self.r3 = ph.circle([], [], fill_color="red", legend="Flagged", size=6)

        self.ui = ui
        self.ui_type = value
        self.set_root(self.p)

    def setup(self):
        self.p = figure(title="Titantuner", plot_height=1000, plot_width=1200,
                x_axis_type="mercator", y_axis_type="mercator", match_aspect=True)
        self.p.title.text_font_size = "25px"
        self.p.title.align = "center"

        tile_provider = get_provider(Vendors.CARTODBPOSITRON)
        self.p.add_tile(tile_provider)

        r1 = self.p.circle([], [], fill_color="gray", legend="OK", size=20)
        r2 = self.p.circle([], [], fill_color="red", legend="Flagged", size=20)
        r1change = self.p.circle([], [], fill_color="gray", line_width=3, size=20)
        r2change = self.p.circle([], [], fill_color="red", line_width=3, size=20)
        source = ColumnDataSource(dict(x=[], y=[], text=[]))
        glyph = Text(x="x", y="y", text="text", text_color="#000000", text_align="center",
                text_baseline="middle")
        t1 = self.p.add_glyph(source, glyph)

        self.set_ui("sct")
        # self.set_ui("isolation")

        self.ds1 = r1.data_source
        self.ds2 = r2.data_source
        self.ds1change = r1change.data_source
        self.ds2change = r2change.data_source
        #self.ds3 = self.r3.data_source
        #self.ds4 = self.r4.data_source
        self.dt1 = t1.data_source

        self.set_root(self.p)
        self.old_flags = None

    def set_root(self, p):
        self.panel = list(self.ui.values())
        # c = column([self.menu] + self.panel)
        c = column(self.panel)

        root = row(self.p, c)
        curdoc().clear()
        curdoc().add_root(root)

    def reset_root(self):
        print("Resetting")
        self.panel = list(self.ui.values())
        c = column(self.panel)

        root = row(self.p, c)
        curdoc().add_root(root)

    def choose_dataset_handler(self, attr, old, new):
        self.set_dataset(new)
        self.set_ui(self.ui_name)

    def choose_test_handler(self, new):
        name = self.id2uiname(new)
        self.set_ui(name)
        self.panel = list(self.ui.values())

    def button_click_callback(self, attr):
        s_time = time.time()

        frac = self.ui["frac"].value
        if frac == 100:
            Is = np.array(range(len(self.lats)))
        else:
            np.random.seed(0)
            Is = np.random.randint(0, len(self.lats), int(frac / 100 * len(self.lats)))

        # if self.latrange is not None and self.lonrange is not None:

        Is0 = np.where((self.lats > self.ui["latrange"].value[0]) & (self.lats < self.ui["latrange"].value[1]) & (self.lons > self.ui["lonrange"].value[0]) & (self.lons < self.ui["lonrange"].value[1]))[0]
        Is = np.intersect1d(Is, Is0)

        yy = self.lat2y(self.lats)
        xx = self.lon2x(self.lons)

        if self.ui_type == "sct":
            nmin = self.ui["nmin"].value
            nmax = self.ui["nmax"].value
            nminprof = self.ui["nminprof"].value
            t2pos = self.ui["t2pos"].value
            t2neg = self.ui["t2neg"].value
            eps2 = self.ui["eps2"].value
            dhmin = self.ui["dhmin"].value
            dzmin = self.ui["dzmin"].value
            dz = self.ui["dz"].value

            # status, flags = titanlib.range_check(self.values, [new[0]], [new[1]])
            # status, flags = titanlib.range_check_climatology(self.lats[Is], self.lons[Is], self.elevs[Is], self.values[Is], 1577836800, [new[1]], [new[0]])

            status, sct, flags = titanlib.sct(self.lats[Is], self.lons[Is], self.elevs[Is], self.values[Is], nmin, nmax, nminprof,
                    dzmin, dhmin, dz, t2pos * np.ones(len(Is)), t2neg * np.ones(len(Is)),
                    eps2 * np.ones(len(Is)))
            sct = np.array(sct)

            texts = []
            for t in range(len(Is)):
                curr = []
                if 0 in self.ui["labels"].active:
                    if self.variable == "rr" and self.values[Is[t]] < 1 and self.values[Is[t]] > 0:
                        curr += ["%.1f" % self.values[Is[t]]]
                    else:
                        curr += ["%d" % self.values[Is[t]]]
                if 1 in self.ui["labels"].active:
                    curr += ["%.1f" % sct[t]]
                if 2 in self.ui["labels"].active:
                    curr += ["%d" % self.elevs[Is[t]]]
                texts += ['\n'.join(curr)]
            if len(self.ui["labels"].active) == 0:
                self.dt1.data = {'y':[], 'x':[], 'text':[]}
            else:
                self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':texts}

        elif self.ui_type == "isolation":
            status, flags = titanlib.isolation_check(self.lats[Is], self.lons[Is], int(self.ui["num"].value), float(self.ui["radius"].value * 1000))
        elif self.ui_type == "buddy":
            status, flags = titanlib.buddy_check(self.lats[Is], self.lons[Is], self.elevs[Is], self.values[Is],
                    [self.ui["distance"].value], [self.ui["num"].value],
                    [self.ui["threshold"].value], self.ui["elev_range"].value,
                    self.ui["elev_gradient"].value / 1000, self.ui["min_std"].value,
                    self.ui["num_iterations"].value)
        elif self.ui_type == "buddy_event":
            status, flags = titanlib.buddy_event_check(self.lats[Is], self.lons[Is], self.elevs[Is], self.values[Is],
                    [self.ui["distance"].value], [self.ui["num"].value],
                    [self.ui["event_threshold"].value],
                    [self.ui["threshold"].value], self.ui["elev_range"].value,
                    self.ui["elev_gradient"].value / 1000)

        if self.ui_type is not "sct":
            texts = []
            for t in range(len(Is)):
                curr = []
                if self.variable == "rr" and self.values[Is[t]] < 1 and self.values[Is[t]] > 0:
                    curr += ["%.1f" % self.values[Is[t]]]
                else:
                    curr += ["%d" % self.values[Is[t]]]
                texts += [curr]
            self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':texts}


        e_time = time.time()
        self.ui["time"].value = "%f" % (e_time- s_time)
        flags = np.array(flags)
        I0 = np.where(flags == 0)[0]
        I1 = np.where(flags == 1)[0]

        y0, x0 = np.histogram(self.values[Is[I0]], bins=self.edges)
        if self.old_flags is None:
            self.ds1.data = {'y':yy[Is[I0]], 'x':xx[Is[I0]]}
            self.ds2.data = {'y':yy[Is[I1]], 'x':xx[Is[I1]]}
        else:
            I0new = np.where((flags == 0) & (self.old_flags == 0))[0]
            I1new = np.where((flags == 1) & (self.old_flags == 1))[0]
            I0change = np.where((flags == 0) & (self.old_flags == 1))[0]
            I1change = np.where((flags == 1) & (self.old_flags == 0))[0]
            self.ds1.data = {'y':yy[Is[I0new]], 'x':xx[Is[I0new]]}
            self.ds2.data = {'y':yy[Is[I1new]], 'x':xx[Is[I1new]]}
            self.ds1change.data = {'y':yy[Is[I0change]], 'x':xx[Is[I0change]]}
            self.ds2change.data = {'y':yy[Is[I1change]], 'x':xx[Is[I1change]]}

        self.ui["mean"].value = "%.1f" % (np.nanmean(self.values[Is[I0]]))
        self.ui["stations"].value = "%d (%.2f %%)" % (len(Is), 100.0 * len(I1) / len(Is))

        # Histogram plot
        # y, x = np.histogram(self.values[Is[I1]], bins=self.edges)
        # self.ds4.data = {'x': self.values[Is[I0]], 'y':  self.elevs[Is[I0]]}
        # self.ds4.data = {'top': y + y0, 'bottom':  0 * y, 'left': self.edges[:-1], 'right': self.edges[1:]}
        # self.ds3.data = {'x': self.values[Is[I1]], 'y':  self.elevs[Is[I]]}

        self.old_flags = copy.deepcopy(flags)

    def set_dataset(self, index):
        index = int(index)
        # names = [dataset["name"] for dataset in self.datasets]
        # index = names.index(name)
        self.dataset_index = index
        self.lats = self.datasets[index]["lats"]
        self.lons = self.datasets[index]["lons"]
        self.elevs = self.datasets[index]["elevs"]
        self.values = self.datasets[index]["values"]
        self.variable = self.datasets[index]["variable"]
        if self.variable == "ta":
            self.units = "C"
        elif self.variable == "rr":
            self.units = "mm/h"
        else:
            raise NotImplementedError

    def __init__(self, datasets):
        self.datasets = datasets
        self.set_dataset(0)

        self.setup()


    def lat2y(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        return np.log(np.tan(math.pi / 4 + np.radians(a) / 2)) * RADIUS

    def lon2x(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        return np.radians(a) * RADIUS

    def uiname2id(self, name):
        if name == "sct":
            return 0
        elif name == "isolation":
            return 1
        elif name == "buddy":
            return 2
        elif name == "buddy_event":
            return 3

    def id2uiname(self, id):
        if id == 0:
            return "sct"
        elif id == 1:
            return "isolation"
        elif id == 2:
            return "buddy"
        elif id == 3:
            return "buddy_event"
