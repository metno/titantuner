import titanlib
import numpy as np
import bokeh.plotting
import metio.titan
import time
import math

from bokeh.io import output_file, show
from bokeh.layouts import column, row, widgetbox, gridplot
from bokeh.models import Button, Title, Text, Label, Panel, ColumnDataSource, GMapOptions
from bokeh.models.widgets import RangeSlider, Slider, PreText, Paragraph, TextInput, Select, RadioButtonGroup
from bokeh.models.widgets.widget import Widget
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc, show, output_file
from bokeh.tile_providers import get_provider, Vendors


class App(object):
    def __init__(self):
        self.ui = None

    def setup(self):
        p = figure(title="Titantuner", plot_height=1000, plot_width=1200,
                x_axis_type="mercator", y_axis_type="mercator")
        p.title.text_font_size = "25px"
        p.title.align = "center"

        tile_provider = get_provider(Vendors.CARTODBPOSITRON)
        p.add_tile(tile_provider)

        r1 = p.circle([], [], fill_color="gray", legend="OK", size=20)
        r2 = p.circle([], [], fill_color="red", legend="Flagged", size=20)
        source = ColumnDataSource(dict(x=[], y=[], text=[]))
        glyph = Text(x="x", y="y", text="text", text_color="#000000", text_align="center",
                text_baseline="middle")
        t1 = p.add_glyph(source, glyph)

        self.sliders = dict()
        # self.sliders["Range"] = RangeSlider(start=-20, end=20, value=[-10,10], step=1, title="Range")
        self.sliders["frac"] = Slider(start=0, end=100, value=100, step=10, title="Fraction of stations (%)")
        self.sliders["t2pos"] = Slider(start=0, end=10, value=4, step=0.1, title="T2pos")
        self.sliders["eps2"] = Slider(start=0, end=2, value=0.5, step=0.1, title="eps2")
        self.sliders["dzmin"] = Slider(start=0, end=200, value=30, step=10, title="dzmin")
        self.sliders["dhmin"] = Slider(start=0, end=20000, value=10000, step=1000, title="dhmin")
        self.sliders["dz"] = Slider(start=100, end=1000, value=200, step=100, title="dz")
        self.sliders["type"] = RadioButtonGroup(labels=["Obs", "SCT", "None"], active=0)
        self.I = None

        ph = figure(title="Histogram") # , plot_height=800, plot_width=1200)
        self.edges = range(-20, 21)

        r4 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="red")
        r3 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="navy")

        self.ds1 = r1.data_source
        self.ds2 = r2.data_source
        self.ds3 = r3.data_source
        self.ds4 = r4.data_source
        self.dt1 = t1.data_source
        button = Button(label="Update")
        button.on_click(self.button_click_callback)
        self.texts = list()
        self.texts += [TextInput(value="None", title="Titanlib request time:")]
        self.texts += [TextInput(value="None", title="% stations removed")]
        # menuitems = [("Climatology check", "clim"), ("Range check", "range")]
        # self.menu = Select(title="Check", value="clim", options=menuitems)
        # self.menu.on_change("value", self.menu_handler)

        print(type(self.sliders.values()))
        self.panel = list(self.sliders.values()) + [button] + self.texts + [ph]
        # c = column([self.menu] + self.panel)
        c = column(self.panel)

        root = row(p, c)
        curdoc().add_root(root)

    def menu_handler(self, attr, old, new):
        self.panel = 1


    def my_text_input_handler(self, attr, old, new):
        s_time = time.time()

        frac = self.sliders["frac"].value
        t2pos = self.sliders["t2pos"].value
        eps2 = self.sliders["eps2"].value
        dhmin = self.sliders["dhmin"].value
        dzmin = self.sliders["dzmin"].value
        dz = self.sliders["dz"].value
        if frac == 100:
            Is = np.array(range(len(self.lats)))
        else:
            np.random.seed(0)
            Is = np.random.randint(0, len(self.lats), int(frac / 100 * len(self.lats)))

        # status, flags = titanlib.range_check(self.values, [new[0]], [new[1]])
        # status, flags = titanlib.range_check_climatology(self.lats[Is], self.lons[Is], self.elevs[Is], self.values[Is], 1577836800, [new[1]], [new[0]])
        import pyproj
        proj = pyproj.Proj("+proj=lcc +lat_0=63 +lon_0=15 +lat_1=63 +lat_2=63 +no_defs +R=6.371e+06")
        x_proj, y_proj = proj(self.lons[Is], self.lats[Is],  inv=True)

        status, sct, flags = titanlib.sct(x_proj, y_proj, self.elevs[Is], self.values[Is], 100, 300, 100,
                dzmin, dhmin, dz, t2pos * np.ones(len(Is)), t2pos * np.ones(len(Is)),
                eps2 * np.ones(len(Is)))
        # status, flags = titanlib.sct([0,1,2,3,4,5,6], [0,1,2,3,4,5,6], [0,0,0,0,0,0,0], [0,1,2,3,4,5,6])
        sct = np.array(sct)

        yy = self.lat2y(self.lats)
        xx = self.lon2x(self.lons)

        e_time = time.time()
        self.texts[0].value = "%f" % (e_time- s_time)
        flags = np.array(flags)
        I = np.where(flags == 0)[0]
        y0, x0 = np.histogram(self.values[Is[I]], bins=self.edges)
        self.ds3.data = {'top': y0, 'bottom': 0 * y0, 'left': self.edges[:-1], 'right': self.edges[1:]}
        # print(len(I), len(flags))
        self.ds1.data = {'y':yy[Is[I]], 'x':xx[Is[I]]}
        # self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':["%d" % int(t) for t in self.values[Is]]}
        if self.sliders["type"].active == 0:
            self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':["%d" % (self.values[Is[t]]) for t in range(len(Is))]}
        elif self.sliders["type"].active == 1:
            self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':["%.1f" % (sct[Is[t]]) for t in range(len(Is))]}
        else:
            self.dt1.data = {'y':[], 'x':[], 'text':[]}
            #self.dt1.data = {'y':yy[Is], 'x':xx[Is], 'text':["%.1f %d" % (sct[Is[t]], self.values[Is[t]]) for t in range(len(Is))]}

        I = np.where(flags == 1)[0]
        y, x = np.histogram(self.values[Is[I]], bins=self.edges)
        self.ds4.data = {'top': y + y0, 'bottom':  0 * y, 'left': self.edges[:-1], 'right': self.edges[1:]}
        self.texts[1].value = "%g %%" % (100.0 * len(I) / len(self.lats))
        self.ds2.data = {'y':yy[Is[I]], 'x':xx[Is[I]]}
    # slider.on_change("value", my_text_input_handler)

    def button_click_callback(self, attr):
        self.my_text_input_handler("value", None, self.sliders["frac"].value)

    def run(self):
        N = 10000

        dataset = metio.titan.get([1580947200], 'ta')
        self.lats = dataset.lats # [0:2000]
        self.lons = dataset.lons # [0:2000]
        self.elevs = dataset.elevs # [0:2000]
        self.values = dataset.values[0, :] # [0, 0:2000]
        I = np.where((self.lats > 59.3) & (self.lats < 60.1) & (self.lons > 10) & (self.lons < 11.1))[0]
        self.lats = self.lats[I]
        self.lons = self.lons[I]
        self.elevs = self.elevs[I]
        self.values = self.values[I]

        p = bokeh.plotting.figure()
        # bokeh.plotting.show(root)


    def lat2y(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        print(a.shape)
        return np.log(np.tan(math.pi / 4 + np.radians(a) / 2)) * RADIUS

    def lon2x(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        return np.radians(a) * RADIUS

# def main():
# if __name__ == "__main__":
try:
    app = App()
    app.setup()
    app.run()
except Exception as e:
    print(e)
#main()
