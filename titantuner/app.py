import titanlib
import numpy as np
import time
import math
import copy

from bokeh.io import output_file, show
from bokeh.layouts import column, row, gridplot
from bokeh.models import Button, Title, Text, Label, Panel, ColumnDataSource, GMapOptions, BoxZoomTool
from bokeh.models.widgets import RangeSlider, Slider, PreText, Paragraph, TextInput, Select, RadioButtonGroup, CheckboxButtonGroup, Dropdown, InputWidget
from bokeh.models.widgets.widget import Widget
from bokeh.models.renderers import TileRenderer
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc, show, output_file
from bokeh.tile_providers import get_provider, Vendors
import bokeh.application
from bokeh.layouts import LayoutDOM
from bokeh.models import ColorPicker
#from bokeh.transform import factor_cmap
import titantuner

displaid_label_buttons = ["Obs", "BoxCoxObs", "Elev", "SCT"]

def apply_BoxCox(values, BoxCox):
    values_to_test = copy.deepcopy(values)
    if BoxCox == 0:
        ix0 = np.where(values == 0)[0]
        values_to_test[ix0] = 0.0001
        values_to_test = np.log(values_to_test)
    elif BoxCox > 0:
        values_to_test = (pow(values, BoxCox) - 1) / BoxCox
    return values_to_test

def displayed_value(variable, value):
    if variable == "rr" and value < 1 and value > 0:
        return f'{value:.1f}'
    else:
        return f'{value:.0f}'

class App():
    def __init__(self, source, doc):
        self.source = source
        self.doc = doc

        self.ui = None
        date, hour = titantuner.unixtime_to_date(time.time() - 2 * 3600)
        self.datetime = date * 100 + hour
        self.set_dataset(0, self.datetime)
        self.setup_initialize()

    def initialize_val_minmax(self, delta_key, Is):
        values_min = self.data['values'][Is] - self.ui[delta_key].value * np.ones(len(Is))
        values_max = self.data['values'][Is] + self.ui[delta_key].value * np.ones(len(Is))
        return values_min, values_max

    def calculate_val_minmax(self, values_min, values_max, delta_key, fact_key, Is, BoxCox):
        values_min[np.where(values_min < 0)[0]] = 0
        values_min_alt = self.data['values'][Is] - self.ui[fact_key].value * np.ones(len(Is)) * self.data['values'][Is]
        values_min_alt[np.where(values_min_alt < 0)[0]] = 0
        ix_min = np.where(values_min_alt < values_min)[0]
        values_min[ix_min] = values_min_alt[ix_min]

        values_max[np.where(values_max < 0)[0]] = 0
        values_max_alt = self.data['values'][Is] + self.ui[fact_key].value * np.ones(len(Is)) * self.data['values'][Is]
        values_max_alt[np.where(values_max_alt < 0)[0]] = 0
        ix_max = np.where(values_max_alt > values_max)[0]
        values_max[ix_max] = values_max_alt[ix_max]
        
        values_min = apply_BoxCox(values_min, BoxCox)
        values_max = apply_BoxCox(values_max, BoxCox)

        return values_min, values_max

    def add_labels(self, Is, obs_values, boxcox_values, sct, xx, yy, elevs):
        selected_labels = [self.ui["labels"].labels[i] for i in self.ui["labels"].active]
        texts = []
        for t in range(len(xx)):
            curr = []
            if "Obs" in selected_labels:
                curr += [displayed_value(self.variable, obs_values[t])]
            if "BoxCoxObs" in selected_labels:
                # boxcox value for previous tests is not stored
                if len(boxcox_values)>0: 
                    curr += ["%.1f" % boxcox_values[t]]
            if "Elev" in selected_labels:
                curr += ["%d" % elevs[t]]
            if "SCT" in selected_labels:
                if len(sct)>0:
                # sct for previous tests is not stored
                    curr += ["%.1f" % sct[t]]
            texts += ['\n'.join(curr)]
        self.data['labels'][Is] = texts

    def set_ui(self, value):
        self.ui_name = value
        ui = dict()

        # Choose dataset/variable
        dropdown = Select(title=self.source.key_label, background="cyan", options=[("%d" % i, name) for i, name in
            enumerate(self.source.keys)], value=str(self.dataset_index))
        dropdown.on_change("value", self.choose_dataset_handler)
        ui["dataset"] = dropdown

        # Choose datetime
        if self.source.requires_time:
            datetime = TextInput(title="Datehour (YYYYMMDDHH in UTC)", value=str(self.datetime))
            datetime.on_change("value", self.choose_datetime_handler)
            ui["datetime"] = datetime

        # Choose the titanlib test

        # Probably possible to get a different displaid name for the option
        # titanlib_tests = [("SCT", "sct"), ("Isolation", "isolation"), ("Buddy", "buddy"),
        #                   ("Buddy event", "buddy_event"), ("SCTres", "sctres"), ("SCTdual", "sctdual"), ("FirstGuess", "fgt")]
        # Can also be done with a dictionary, but I think it exists a more compact syntax using duple
        titanlib_tests = ["sctdual", "buddy_event", "buddy", "sct", "isolation", "sctres", "fgt"]

        dropdown = Select(title="Type of test", background="cyan", options=titanlib_tests, aspect_ratio=2, value=self.ui_name)
        dropdown.on_change("value", self.choose_test_handler)
        value = dropdown.value
        ui["type"] = dropdown

        ui["frac"] = Slider(start=0, end=100, value=100, step=10, title="Fraction of stations to use [%]")

        # Set the viewing domain based on the available stations
        if len(self.lats) == 0:
            latrange = [0, 10]
            lonrange = [0, 10]
        elif len(self.lats) == 1:
            latrange = [np.floor(np.min(self.lats)) - 1, np.ceil(np.max(self.lats)) + 1]
            lonrange = [np.floor(np.min(self.lons)) - 1, np.ceil(np.max(self.lons)) + 1]
        else:
            latrange = [np.floor(np.min(self.lats)), np.ceil(np.max(self.lats))]
            lonrange = [np.floor(np.min(self.lons)), np.ceil(np.max(self.lons))]

        ui["latrange"] = RangeSlider(start=latrange[0], end=latrange[1], value=latrange, step=0.1, title="Latitude range")
        ui["lonrange"] = RangeSlider(start=lonrange[0], end=lonrange[1], value=lonrange, step=0.1, title="Longitude range")

        # Test specifics
        # SCT
        if value == "sct":
            ui["nmin"] = Slider(start=5, end=1000, value=5, step=10, title="Minimum obs in box")
            ui["nmax"] = Slider(start=10, end=300, value=20, step=10, title="Maximum obs in box")
            ui["inner_radius"] = Slider(start=100, end=100000, value=4000, step=100, title="Inner radius [m]")
            ui["outer_radius"] = Slider(start=100, end=200000, value=10000, step=100, title="Outer radius [m]")
            ui["niterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            ui["nminprof"] = Slider(start=50, end=1000, value=100, step=50, title="Minimum obs to fit profile")
            ui["t2pos"] = Slider(start=0, end=10, value=4, step=0.1, title="T2pos")
            ui["t2neg"] = Slider(start=0, end=10, value=4, step=0.1, title="T2neg")
            ui["eps2"] = Slider(start=0, end=2, value=0.5, step=0.1, title="eps2")
            ui["dzmin"] = Slider(start=0, end=200, value=30, step=10, title="Min elev range to fit profile [m]")
            ui["dhmin"] = Slider(start=0, end=20000, value=10000, step=1000, title="Min horiz OI distance [m]")
            ui["dz"] = Slider(start=100, end=1000, value=200, step=100, title="Vertical OI distance [m]")
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons, active=[0])

            #self.r4 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="red")
            #self.r3 = ph.quad(top=[1,2,3], bottom=0, left=self.edges[:-1], right=self.edges[1:], fill_color="navy")
        # end SCT

        # SCT resistant begin
        elif value == "sctres":
            ui["nmin"] = Slider(start=5, end=1000, value=5, step=10, title="Minimum obs in box")
            ui["nmax"] = Slider(start=100, end=3000, value=100, step=100, title="Maximum obs in box")
            ui["inner_radius"] = Slider(start=100, end=100000, value=4000, step=100, title="Inner radius [m]")
            ui["outer_radius"] = Slider(start=100, end=200000, value=10000, step=100, title="Outer radius [m]")
            ui["niterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            ui["nminprof"] = Slider(start=50, end=1000, value=100, step=50, title="Minimum obs to fit profile")
            ui["t2pos"] = Slider(start=0, end=10, value=4, step=0.1, title="T2pos")
            ui["t2neg"] = Slider(start=0, end=10, value=4, step=0.1, title="T2neg")
            ui["eps2"] = Slider(start=0, end=2, value=0.5, step=0.1, title="eps2")
            ui["dzmin"] = Slider(start=0, end=200, value=30, step=10, title="Min elev range to fit profile [m]")
            ui["dhmin"] = Slider(start=0, end=20000, value=10000, step=1000, title="Min horiz OI distance [m]")
            ui["dhmax"] = Slider(start=0, end=20000, value=10000, step=1000, title="Max horiz OI distance [m]")
            ui["kth"] = Slider(start=1, end=200, value=10, step=1, title="use the k-th closest obs for horiz OI distance")
            ui["dz"] = Slider(start=100, end=1000, value=200, step=100, title="Vertical OI distance [m]")
            ui["a_delta"] = Slider(start=0, end=100, value=10, step=1, title="Define range of allowed values (additive)")
            ui["a_fact"] = Slider(start=0, end=10, value=1, step=.1, title="Define range of allowed values (multiplicative)")
            ui["v_delta"] = Slider(start=0, end=10, value=0.1, step=.1, title="Define range of valid values (additive)")
            ui["v_fact"] = Slider(start=0, end=1, value=0.05, step=.01, title="Define range of valid values (multiplicative)")
            ui["background_elab"] = RadioButtonGroup(labels=["VerticalProfile", "VerticalProfileTheilSen", "MeanOuterCircle", "MedianOuterCircle", "External"], active=0)
            ui["basic"] = RadioButtonGroup(labels=["Basic", "NOT Basic"], active=0)
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons, active=[0])
        # SCT resistant end

        # SCT dual begin
        elif value == "sctdual":
            ui["nmin"] = Slider(start=5, end=1000, value=5, step=10, title="Minimum obs in box")
            ui["nmax"] = Slider(start=10, end=3000, value=100, step=10, title="Maximum obs in box")
            ui["inner_radius"] = Slider(start=100, end=100000, value=4000, step=100, title="Inner radius [m]")
            ui["outer_radius"] = Slider(start=100, end=200000, value=10000, step=100, title="Outer radius [m]")
            ui["niterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            ui["t_event"] = Slider(start=0, end=5, value=0.1, step=0.1, title="Event threshold")
            ui["t_condition"] = RadioButtonGroup(labels=["Eq", "Gt", "Geq", "Lt", "Leq"], active=1)
            ui["t_test"] = Slider(start=0, end=1, value=0.1, step=0.1, title="Test threshold")
            ui["dhmin"] = Slider(start=0, end=20000, value=5000, step=1000, title="Min horiz OI distance [m]")
            ui["dhmax"] = Slider(start=0, end=20000, value=50000, step=1000, title="Max horiz OI distance [m]")
            ui["kth"] = Slider(start=1, end=200, value=3, step=1, title="use the k-th closest obs for horiz OI distance")
            ui["dz"] = Slider(start=100, end=1000, value=10000, step=100, title="Vertical OI distance [m]")
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons[0:-1], active=[0])
        # SCT dual end

        # FGT begin
        elif value == "fgt":
            ui["nmin"] = Slider(start=5, end=1000, value=5, step=10, title="Minimum obs in box")
            ui["nmax"] = Slider(start=100, end=3000, value=100, step=100, title="Maximum obs in box")
            ui["inner_radius"] = Slider(start=100, end=100000, value=4000, step=100, title="Inner radius [m]")
            ui["outer_radius"] = Slider(start=100, end=200000, value=10000, step=100, title="Outer radius [m]")
            ui["niterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            ui["nminprof"] = Slider(start=50, end=1000, value=100, step=50, title="Minimum obs to fit profile")
            ui["tpos"] = Slider(start=0, end=10, value=4, step=0.1, title="T2pos")
            ui["tneg"] = Slider(start=0, end=10, value=4, step=0.1, title="T2neg")
            ui["dzmin"] = Slider(start=0, end=200, value=30, step=10, title="Min elev range to fit profile [m]")
            ui["a_delta"] = Slider(start=0, end=100, value=10, step=1, title="Define range of allowed values (additive)")
            ui["a_fact"] = Slider(start=0, end=10, value=1, step=.1, title="Define range of allowed values (multiplicative)")
            ui["v_delta"] = Slider(start=0, end=10, value=0.1, step=.1, title="Define range of valid values (additive)")
            ui["v_fact"] = Slider(start=0, end=1, value=0.05, step=.01, title="Define range of valid values (multiplicative)")
            ui["background_elab"] = RadioButtonGroup(labels=["VerticalProfile", "VerticalProfileTheilSen", "MeanOuterCircle", "MedianOuterCircle", "External"], active=0)
            ui["basic"] = RadioButtonGroup(labels=["Basic", "NOT Basic"], active=0)
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons, active=[0])
        # FGT end

        # Isolation test, begin
        elif value == "isolation":
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Number of additional observations")
            ui["radius"] = Slider(start=0.25, end=50, value=15, step=0.25, title="Radius [km]")
            ui["labels"] = CheckboxButtonGroup(labels=[displaid_label_buttons[0], displaid_label_buttons[2]], active=[0])
        # Isolation test, end
        
        # Buddy check, begin
        elif value == "buddy":
            ui["distance"] = Slider(start=1000, end=100000, value=5000, step=1000, title="Distance limit [m]")
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Minimum obs required")
            ui["threshold"] = Slider(start=0.1, end=5, value=2, step=0.1, title="Threshold")
            ui["elev_range"] = Slider(start=100, end=1000, value=300, step=100, title="Maximum elevation difference [m]")
            ui["elev_gradient"] = Slider(start=-5, end=10, value=6.5, step=0.5, title="Elevation gradient [%s/km]" % self.units)
            ui["min_std"] = Slider(start=0.1, end=5, value=1, step=0.1, title="Minimum neighbourhood std [%s]" % self.units)
            ui["num_iterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons[0:-1], active=[0])
        # Buddy check, end

        # Buddy-event check, begin
        elif value == "buddy_event":
            ui["distance"] = Slider(start=1000, end=100000, value=5000, step=1000, title="Distance limit [m]")
            ui["num"] = Slider(start=1, end=10, value=5, step=1, title="Minimum obs required")
            ui["event_threshold"] = Slider(start=0, end=5, value=0.2, step=0.1, title="Event threshold")
            ui["threshold"] = Slider(start=0.05, end=5, value=0.1, step=0.05, title="Threshold")
            ui["elev_range"] = Slider(start=100, end=1000, value=300, step=100, title="Maximum elevation difference [m]")
            ui["elev_gradient"] = Slider(start=-5, end=10, value=0, step=0.5, title="Elevation gradient [%s/km]" % self.units)
            ui["num_iterations"] = Slider(start=1, end=10, value=1, step=1, title="Number of iterations")
            if self.variable == 'rr':
                ui["BoxCox"] = Slider(start=-0.1, end=1, value=-1, step=.1, title="Box-Cox power (unactive if BoxCox<0 or val <0)")
            ui["labels"] = CheckboxButtonGroup(labels=displaid_label_buttons[0:-1], active=[0])
        # Buddy-event check, end

        ui["time"] = TextInput(value="None", title="Titanlib request time [s]")
        ui["stations"] = TextInput(value="None", title="Stations: total | removed | new flagged | new unflag.")
        ui["mean"] = TextInput(value="None", title="Average observed [%s]" % self.units)

        # Choose test combinaison
        dropdown = Select(title="Combine test with previous test", background="cyan", options=list(dico_combine_test_code2ui.values()), 
                          value= dico_combine_test_code2ui[self.combine_test])
        dropdown.on_change("value", self.choose_combine_test_handler)
        ui["combine_test"] = dropdown

        # Options: https://docs.bokeh.org/en/latest/docs/reference/tile_providers.html
        # STAMEN_TERRAIN and STAMEN_TONER Not anymore available
        #dropdown = Select(title="Map background", options=[(Vendors.CARTODBPOSITRON, "Positron"),
        #    (Vendors.STAMEN_TERRAIN, "Terain"),
        #    (Vendors.STAMEN_TONER, "Toner")])
        #dropdown.on_change("value", self.choose_background_handler)
        #ui["background"] = dropdown
        self.ui = ui
        self.set_apply_button()
        #ph = figure(title="Histogram") # , plot_height=800, plot_width=1200)
        #ui["histogram"] = ph
        self.edges = range(-20, 21)

        #self.r4 = ph.circle([], [], fill_color="gray", legend="OK", size=3)
        #self.r3 = ph.circle([], [], fill_color="red", legend="Flagged", size=6)

        self.ui_type = value
        self.set_root(self.p)

    def data_initialize(self):
        n = len(self.lon2x(self.lons))
        self.data = {'x': self.lon2x(self.lons),
                    'y': self.lat2y(self.lats),
                    'test_code': np.full(n, -99),
                    'flagged_least1': np.full(n, False),
                    'flagged_new': np.full(n, False),
                    'unflagged_new': np.full(n, False),
                    'values':self.values,
                    'labels': np.array([displayed_value(self.variable, val) for val in self.values]).astype(str)}
    
    def plot_config(self, plot_orange_if_possible=True):
        # Mercator axes don't seem to work on some systems
        # self.p = figure(title="Titantuner", plot_height=1000, plot_width=1200,
        #         x_axis_type="mercator", y_axis_type="mercator", match_aspect=True)
        # BUG: strech_both does not strech in height, thus adding the height manually
        self.p = figure(tools="pan,wheel_zoom,save,reset", title="Titantuner", sizing_mode='stretch_both', match_aspect=True, height=1200)
        self.p.add_tools(BoxZoomTool(match_aspect=True))
        self.p.title.text_font_size = "25px"
        self.p.title.align = "center"

        tile_provider = get_provider(Vendors.CARTODBPOSITRON)
        self.p.add_tile(tile_provider)

        data_test = {'x':np.array([1e6, 1e6, 1e6]),
                                 'y':np.array([8.8e6, 8.7e6, 8.6e6]),
                                 'test_code': np.array([0, -99, 0]),
                                'values': np.array([40, 40, 40])}
        

        if self.combine_test != "chain" and self.number_tests>0:
            flag_to_plot = [-99, self.number_tests -1]
        else:
            flag_to_plot = np.sort(np.unique(self.data['test_code']))
        for test in flag_to_plot:
            Itest = np.where(self.data["test_code"]==test)[0]
            if test != -99:
                color = self.colors[np.mod(test, len(self.colors))]
                #if (self.number_tests >0 and self.combine_test == "chain"):
                #if test != self.number_tests:
                if self.combine_test == "chain" or self.combine_test == "single":
                    test_name = self.dico_test_code2type[test]
                else:
                    test_name = self.dico_test_code2type[test] + " combined to previous"
                if self.combine_test != "chain":
                    test_in_legend = test_name
                else:
                    test_in_legend = f"{test} ({test_name})"
                if(len(Itest)>0):
                    legend_txt = f'Flagged by test {test_in_legend}'
                else:
                    legend_txt = f'No value flagged by test {test_in_legend})'
            else:
                color = "lightgray"
                legend_txt = 'OK / Not tested'
            self.p.scatter('x', 'y', source={'x': self.data['x'][Itest],
                                             'y': self.data['y'][Itest]
                                            },
            fill_alpha=0.9, size=14,
            marker='circle',
            line_width = 1,
            color=color,
            legend_label=legend_txt,
            line_color="darkblue"
        )
        # # Note: if doing the plots of markers + orange lines in one command, 
        # some legend and overlay properties are difficult to set up 
        # if using the code below, 'test_code' data has to be str (data['test_code'].astype(str))
        # https://docs.bokeh.org/en/2.4.3/docs/user_guide/data.html
        #            self.p.scatter('x', 'y', source=self.data,
        #    legend_group="test_code",
        #    fill_alpha=0.9, size=12,
        #    marker='circle',
        #    line_width = 0,
        #    color=factor_cmap('test_code', self.colors, test_code_uniq, nan_color='lightgray'),
        #    line_color =factor_cmap('flagged_least1', line_color, flagged_least1_uniq)
        #)
        
        if self.old_flags is not None and self.combine_test != "chain" and plot_orange_if_possible==True :
            flagged_change_plot = self.p.scatter([], [],
                    size=16,
                    marker='circle',
                    line_color = 'orange',
                    color=None,
                    line_width = 2,
                    legend_label="flag changed by last test"
                    )
            Ichange = np.where( (self.data['unflagged_new'] | self.data['flagged_new']))
            flagged_change_plot.data_source.data = {"x": self.data['x'][Ichange] , "y": self.data['y'][Ichange]}

            # flagged_least1_plot = self.p.scatter([], [],
            # fill_alpha=0, size=13,
            # marker='circle',
            # line_color = "red",
            # line_width = 2,
            # legend_label="flagged at least once"
            # )

                #Ileast1 = np.where( self.data['flagged_least1'])
                
                #flagged_least1_plot.data_source.data = {"x": self.data['x'][Ileast1] , "y": self.data['y'][Ileast1]}

        marker_labels = self.p.text('x', 'y',
                        font_size="7pt",
                        text_font_style = 'bold',
                        text_color="#000000",
                        text_align="center",
                        text_baseline="middle",
                        text='labels',
                        source=self.data
                     )
        source = ColumnDataSource(dict(x=[], y=[], text=[]))
        glyph = Text(x="x", y="y", text="text", text_color="#000000", text_align="center",
                text_baseline="middle")
        t1 = self.p.add_glyph(source, glyph)
        t1.level = "overlay"

        self.p.legend.location = "top_left"
        self.p.legend.title = "Test type"

    def color_picker_initialize(self):
        picker = ColorPicker(title="Color of the last flagged points", color="red", aspect_ratio=2)
        picker.on_change("color", self.set_marker_color)
        self.picker = picker
    
    def setup_initialize(self):
        self.number_tests = 0
        self.marker_color = "red"
        self.colors = ["red", "green", "cyan", "magenta", "blue", "gold", "brown"]
        self.old_flags = None
        self.dico_test_code2type = {0: None}
        self.data_initialize()
        self.combine_test = "single"
        self.plot_config(plot_orange_if_possible=False)
        self.color_picker_initialize()
        self.set_ui("sctdual")
        self.set_root(self.p)
      

    def set_root(self, p):
        self.panel = [v for v in self.ui.values() if v if isinstance(v, LayoutDOM)]
        c1 = column(self.panel) 
        # NOTE: Not sure why column(self.panel, self.picker) does not work!
        c0 = column(self.p, self.picker)
        c0.sizing_mode = "stretch_both"
        root = row(c0, c1)
        self.doc.clear()
        self.doc.add_root(root)

    def reset_root(self):
        return
        print("Resetting")
        self.panel = [v for v in self.ui.values() if v if isinstance(v, LayoutDOM)]
        c = column(self.panel)
        root = row(self.p, c)
        curdoc().add_root(root)

    def choose_dataset_handler(self, attr, old, new):
        self.set_dataset(int(new), self.datetime)
        self.setup_initialize()
       # self.set_ui(self.ui_name)


    def choose_datetime_handler(self, attr, old, new):
        new = int(new)
        self.datetime = new
        self.set_dataset(self.dataset_index, new)
        self.set_ui(self.ui_name)

    def choose_background_handler(self, attr, old, new):
        self.set_background(new)
        # self.set_ui(self.ui_name)

    def set_marker_color(self, attr, old, new):
        #  change the initial color for the picker without changing the color of the last plotted markers
        # self.keep_color_marker = True # Forcing not triggering the content of the on_change function linked to the picker
        # NOTE Ideally the picker should only change the color, not refresh all the points,
        # (only change the color glyph of the right glyph, but to do so one need to store/find back the name/id of the glyph) 
        if(self.keep_color_marker==False):
            self.marker_color = new
            if(len(self.colors)>self.number_tests):
                self.colors[self.number_tests-1] = new
            else:
                self.colors.append(new)
            self.plot_config(plot_orange_if_possible=True)
            self.set_root(self.p)



    def choose_test_handler(self, attr, old, new):
        name = new
        self.set_ui(name)
        self.panel = list(self.ui.values())
    
    def choose_combine_test_handler(self, attr, old, new):
        self.combine_test = dico_combine_test_ui2code[new]

    def button_apply_click(self, attr):
        self.ui["apply_button"].button_type = "warning"
        self.ui["apply_button"].label = "Busy"
        self.doc.add_next_tick_callback(self.apply_test)

    def set_apply_button(self):
        label_button = "Apply test"
        button_ui_name = "apply_button"
        if button_ui_name not in self.ui:
            button = Button(button_type="success", label=label_button)
            button.on_click(self.button_apply_click)
            self.ui[button_ui_name] = button
        else:
            self.ui[button_ui_name].label = label_button
            self.ui[button_ui_name].button_type = "success"

    def apply_test(self):
        if self.combine_test == "single":
            self.number_tests = 0

        self.dico_test_code2type[self.number_tests] = self.ui_type
        if (self.number_tests >0 and self.combine_test == "chain"):
            # change the initial color for the picker without changing the color of the last plotted markers
            self.keep_color_marker = True # Forcing not triggering the content of the on_change function linked to the picker
            self.picker.color = self.colors[np.mod(self.number_tests, len(self.colors))]
        self.keep_color_marker = False

        print(f"Number of test combined: {self.number_tests} "\
              f"combination chosen: {dico_combine_test_code2ui[self.combine_test]}, test type: {self.ui_type}, color {self.marker_color}")

        s_time = time.time()

        self.last_latrange = self.ui["latrange"].value
        self.last_lonrange = self.ui["lonrange"].value
        yy = self.lat2y(self.lats)
        xx = self.lon2x(self.lons)
        values_to_test = self.values

        frac = self.ui["frac"].value
        if len(self.lats) == 0:
            Ifrac = []
        else:
            if frac == 100:
                Ifrac = np.array(range(len(self.lats)))
            else:
                np.random.seed(0)
                Ifrac = np.random.randint(0, len(self.lats), int(frac / 100 * len(self.lats)))

        # if self.latrange is not None and self.lonrange is not None:

        Icoord = np.where((self.lats > self.ui["latrange"].value[0]) & (self.lats < self.ui["latrange"].value[1]) & (self.lons > self.ui["lonrange"].value[0]) & (self.lons < self.ui["lonrange"].value[1]))[0]
        Iall_tests = np.intersect1d(Ifrac, Icoord)
        if self.number_tests == 0 or len(Iall_tests) != len(self.data['x']):
            if len(Iall_tests) != len(self.data['x']) and self.combine_test != "single":
                print("Warning: can't combine with previous tests as the lat/lon selection or the fraction of data is not similar to those used in the previous tests")
                print('Change test type to', {dico_combine_test_code2ui["single"]})
                self.combine_test = "single"
                self.number_tests = 0
            # start with reinitializing data
            self.data['x'] = xx[Iall_tests]
            self.data['y'] = yy[Iall_tests]
            n_data = len(Iall_tests)
            self.data['test_code'] = np.full(n_data, -99)
            self.data['flagged_least1'] = np.full(n_data, False)
            self.data['flagged_new'] = np.full(n_data, False)
            self.data['unflagged_new'] = np.full(n_data, False)
            self.data['values'] = values_to_test[Iall_tests]
            self.data['labels'] = values_to_test[Iall_tests].astype(str)
           # self.old_flags = None

        if self.combine_test == "chain":
            Is = np.where(self.data['test_code']==-99)[0]
            print(f"start, chained on indexes", Is)
        else:
            Is = np.array(range(len(Iall_tests)))
            #print(f"start test on indexes", Is)

        if len(Is) == 0:
            self.set_apply_button()
            return

        is_obs_to_check = np.ones(len(Is))
        yy_Is = yy[Iall_tests][Is]
        xx_Is = xx[Iall_tests][Is]
        elevs_Is = self.elevs[Iall_tests][Is]
        values_to_test_Is = values_to_test[Iall_tests][Is]
        points = titanlib.Points(self.lats[Iall_tests][Is], self.lons[Iall_tests][Is], elevs_Is)

        #----------------------------------------------------------------------
        if self.ui_type == "sct":
            nmin = self.ui["nmin"].value
            nmax = self.ui["nmax"].value
            inner_radius = self.ui["inner_radius"].value
            outer_radius = self.ui["outer_radius"].value
            niterations = self.ui["niterations"].value
            nminprof = self.ui["nminprof"].value
            t2pos = self.ui["t2pos"].value
            t2neg = self.ui["t2neg"].value
            eps2 = self.ui["eps2"].value
            dhmin = self.ui["dhmin"].value
            dzmin = self.ui["dzmin"].value
            dz = self.ui["dz"].value
            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                values_to_test_Is = apply_BoxCox(values_to_test_Is, self.ui["BoxCox"].value)

            # flags = titanlib.range_check(self.values, [new[0]], [new[1]])
            # flags = titanlib.range_check_climatology(self.lats[Is], self.lons[Is], elevs_Is, self.data['values'][Is], 1577836800, [new[1]], [new[0]])

            flags, sct, rep = titanlib.sct(points, values_to_test_Is, nmin, nmax, inner_radius,
                    outer_radius, niterations, nminprof,
                    dzmin, dhmin, dz, t2pos * np.ones(len(Is)), t2neg * np.ones(len(Is)),
                    eps2 * np.ones(len(Is)))

            sct = np.array(sct)
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, sct, xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        if self.ui_type == "sctres":
            nmin = self.ui["nmin"].value
            nmax = self.ui["nmax"].value
            inner_radius = self.ui["inner_radius"].value
            outer_radius = self.ui["outer_radius"].value
            niterations = self.ui["niterations"].value
            nminprof = self.ui["nminprof"].value
            t2pos = self.ui["t2pos"].value
            t2neg = self.ui["t2neg"].value
            eps2 = self.ui["eps2"].value
            dhmin = self.ui["dhmin"].value
            dhmax = self.ui["dhmax"].value
            kth = self.ui["kth"].value
            dzmin = self.ui["dzmin"].value
            dz = self.ui["dz"].value

            values_mina, values_maxa = self.initialize_val_minmax("a_delta", Is)
            values_minv, values_maxv = self.initialize_val_minmax("v_delta", Is)

            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                BoxCox = self.ui["BoxCox"].value
                values_to_test_Is = apply_BoxCox(values_to_test_Is, BoxCox)
                values_mina, values_maxa = self.calculate_val_minmax(values_mina, values_maxa, "a_delta", "a_fact", Is, BoxCox)
                values_minv, values_maxv = self.calculate_val_minmax(values_minv, values_maxv, "v_delta", "v_fact", Is, BoxCox)
                values_to_test_Is = apply_BoxCox(values_to_test_Is, BoxCox)

            if self.ui["basic"].active == 0:
                basic=True
            elif self.ui["basic"].active == 1:
                basic=False

            background_values = np.ones(len(Is))
            debug=False

            if self.ui["background_elab"].active == 0:
                background_elab=titanlib.VerticalProfile
            if self.ui["background_elab"].active == 1:
                background_elab=titanlib.VerticalProfileTheilSen
            if self.ui["background_elab"].active == 2:
                background_elab=titanlib.MeanOuterCircle
            if self.ui["background_elab"].active == 3:
                background_elab=titanlib.MedianOuterCircle
 
            # flags = titanlib.range_check(self.values, [new[0]], [new[1]])
            # flags = titanlib.range_check_climatology(self.lats[Is], self.lons[Is], elevs_Is, self.data['values'][Is], 1577836800, [new[1]], [new[0]])

            print("SCT res shape", values_to_test_Is.shape, points.get_lats().shape, len(Is), Is,  np.ones(len(Is)).shape)
            flags, sct = titanlib.sct_resistant(points, values_to_test_Is, 
                    is_obs_to_check, background_values, background_elab,
                    nmin, nmax, inner_radius,
                    outer_radius, niterations, nminprof,
                    dzmin, dhmin, dhmax, kth, dz,
                    values_mina, values_maxa, values_minv, values_maxv,
                    eps2 * np.ones(len(Is)),
                    t2pos * np.ones(len(Is)), t2neg * np.ones(len(Is)),
                    debug, basic )

            sct = np.array(sct)
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, sct, xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        if self.ui_type == "sctdual":
            nmin = self.ui["nmin"].value
            nmax = self.ui["nmax"].value
            inner_radius = self.ui["inner_radius"].value
            outer_radius = self.ui["outer_radius"].value
            niterations = self.ui["niterations"].value
            dhmin = self.ui["dhmin"].value
            dhmax = self.ui["dhmax"].value
            kth = self.ui["kth"].value
            dz = self.ui["dz"].value
            t_event = self.ui["t_event"].value
            t_test = self.ui["t_test"].value

            if self.ui["t_condition"].active == 0:
                t_condition=titanlib.Eq
            if self.ui["t_condition"].active == 1:
                t_condition=titanlib.Gt
            if self.ui["t_condition"].active == 2:
                t_condition=titanlib.Geq
            if self.ui["t_condition"].active == 3:
                t_condition=titanlib.Lt
            if self.ui["t_condition"].active == 4:
                t_condition=titanlib.Leq

            debug=False
            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                values_to_test_Is = apply_BoxCox(values_to_test_Is, self.ui["BoxCox"].value)

            flags = titanlib.sct_dual(points, values_to_test_Is,
                    is_obs_to_check, t_event* np.ones(len(Is)), t_condition,
                    nmin, nmax, inner_radius,
                    outer_radius, niterations,
                    dhmin, dhmax, kth, dz,
                    t_test * np.ones(len(Is)),
                    debug )
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, [], xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        if self.ui_type == "fgt":
            nmin = self.ui["nmin"].value
            nmax = self.ui["nmax"].value
            inner_radius = self.ui["inner_radius"].value
            outer_radius = self.ui["outer_radius"].value
            niterations = self.ui["niterations"].value
            nminprof = self.ui["nminprof"].value
            tpos = self.ui["tpos"].value
            tneg = self.ui["tneg"].value
            dzmin = self.ui["dzmin"].value
            values_mina, values_maxa = self.initialize_val_minmax("a_delta", Is)
            values_minv, values_maxv = self.initialize_val_minmax("v_delta", Is)
            
            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                BoxCox = self.ui["BoxCox"].value
                values_to_test_Is = apply_BoxCox(values_to_test_Is, self.ui["BoxCox"].value)
                values_mina, values_maxa = self.calculate_val_minmax(values_mina, values_maxa, "a_delta", "a_fact", Is, BoxCox)
                values_minv, values_maxv = self.calculate_val_minmax(values_minv, values_maxv, "v_delta", "v_fact", Is, BoxCox)
                values_to_test_Is = apply_BoxCox(values_to_test_Is, BoxCox)

            if self.ui["basic"].active == 0:
                basic=True
            elif self.ui["basic"].active == 1:
                basic=False

            background_values = np.ones(len(Is))
            background_uncertainties = np.ones(len(Is))
            debug=False

            if self.ui["background_elab"].active == 0:
                background_elab=titanlib.VerticalProfile
            if self.ui["background_elab"].active == 1:
                background_elab=titanlib.VerticalProfileTheilSen
            if self.ui["background_elab"].active == 2:
                background_elab=titanlib.MeanOuterCircle
            if self.ui["background_elab"].active == 3:
                background_elab=titanlib.MedianOuterCircle
 
            flags, sct = titanlib.fgt(points, values_to_test_Is, 
                    is_obs_to_check, background_values, 
                    background_uncertainties, background_elab,
                    nmin, nmax, inner_radius,
                    outer_radius, niterations, nminprof, dzmin, 
                    values_mina, values_maxa, values_minv, values_maxv,
                    tpos * np.ones(len(Is)), tneg * np.ones(len(Is)),
                    debug, basic)

            sct = np.array(sct)
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, sct, xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        elif self.ui_type == "isolation":
            flags = titanlib.isolation_check(points, int(self.ui["num"].value), float(self.ui["radius"].value * 1000))
            self.add_labels(Is, self.data['values'][Is], [], [], xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        elif self.ui_type == "buddy":
            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                values_to_test_Is = apply_BoxCox(values_to_test_Is, self.ui["BoxCox"].value)         
            flags = titanlib.buddy_check(points, values_to_test_Is,
                    [self.ui["distance"].value], [self.ui["num"].value],
                    self.ui["threshold"].value, self.ui["elev_range"].value,
                    self.ui["elev_gradient"].value / 1000, self.ui["min_std"].value,
                    self.ui["num_iterations"].value)
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, [], xx_Is, yy_Is, elevs_Is)

        #----------------------------------------------------------------------
        elif self.ui_type == "buddy_event":
            if "BoxCox" in self.ui and self.ui["BoxCox"].value >= 0:
                values_to_test_Is = apply_BoxCox(values_to_test_Is, self.ui["BoxCox"].value)
            flags = titanlib.buddy_event_check(points, values_to_test_Is,
                    [self.ui["distance"].value], [self.ui["num"].value],
                    self.ui["event_threshold"].value,
                    self.ui["threshold"].value, self.ui["elev_range"].value,
                    self.ui["elev_gradient"].value / 1000,
                    self.ui["num_iterations"].value)
            self.add_labels(Is, self.data['values'][Is], values_to_test_Is, [], xx_Is, yy_Is, elevs_Is)
        #----------------------------------------------------------------------
        elif self.ui_type is None:
            flags = np.zeros(len(Is))

        e_time = time.time()
        self.ui["time"].value = "%f" % (e_time- s_time)
        flags = np.array(flags)

        for t in range(len(flags)):
          if flags[t] != 0 and flags[t] != 1:
              flags[t] = 0

        I0 = np.where(flags == 0)[0]
        I1 = np.where(flags == 1)[0]

        #y0, x0 = np.histogram(self.values[Is[I0]], bins=self.edges)
        if self.combine_test !="chain" and self.old_flags is not None and (flags.shape != self.old_flags.shape):
            print(f"CAUTION here is old flag reinitialized to None, flags and old flags don't have the same size")
            if self.old_flags is not None:
                print(flags.shape, self.old_flags.shape)
            self.old_flags = None
        if self.old_flags is None or self.combine_test =="chain":
            if(self.old_flags is None):
                self.ui["stations"].value = "%d | %d (%.2f %%) | NA | NA" % (len(Is), len(I1), 100.0 * len(I1) / len(Is))
            elif self.combine_test =="chain":
                # CAUTION: at this stage test_code is not yet updated with the last new values
                Iflagged_all_tests = np.where(self.data['test_code'] != -99)[0]
                self.ui["stations"].value = "%d | %d (%.2f %%) | %d | 0" % (len(Iall_tests), len(Iflagged_all_tests) + len(I1),
                                                                             100.0 * (len(Iflagged_all_tests) + len(I1)) / len(Is), (len(I1)))
            self.data['flagged_new'][I1] = np.full(len(I1), True)
        else:
            # flag = 1 -> not OK
            # flag = 0 -> OK or unconclusive test
            if self.combine_test == "combineOK_if_1_OK":
               # keep data if it passes one of the tests 
               # OK1 or OK2 -> OK
               flags = (~((flags==0) | (self.old_flags==0))).astype(int)
            elif self.combine_test == "combineOK_if_both_OK": 
                # keep data only if none of the tests flag it 
                # (OK1 and OK2) -> OK
                flags = (~((flags==0) & (self.old_flags==0))).astype(int)
            elif self.combine_test == "combineBad_if_1_Bad": 
               # reject data if flagged by one of the tests, keep the others 
               # (BAD1 or BAD2) -> BAD
               flags = ((flags==1) | (self.old_flags==1)).astype(int)
            elif self.combine_test == "combineBad_if_both_Bad":
                # reject data only if it passes none of the tests
                # (BAD1 and BAD2) -> BAD
                flags = ((flags==1) & (self.old_flags==1)).astype(int)
            I0change = np.where((flags == 0) & (self.old_flags == 1))[0]
            I1change = np.where((flags == 1) & (self.old_flags == 0))[0]
            self.data['flagged_new'][I1change] = np.full(len(I1change), True)
            self.data['unflagged_new'][I0change] = np.full(len(I0change), True)
            I0 = np.where(flags == 0)[0]
            I1 = np.where(flags == 1)[0]
            self.ui["stations"].value = "%d | %d (%.2f %%) | %d | %d" % (len(Is), len(I1), 100.0 * len(I1) / len(Is), len(I1change), len(I0change))
        
        Iflagged_all_tests = np.where(self.data['test_code'] != -99)[0]
        self.data['test_code'][Is[I1]] = np.full(len(I1), self.number_tests)
        Iflagged_all_tests = np.where(self.data['test_code'] != -99)[0]

        self.data['flagged_least1'][Is[I1]] = np.full(len(I1), True)
        self.plot_config(plot_orange_if_possible=True)
        self.set_root(self.p)
        self.ui["mean"].value = "%.1f" % (np.nanmean(values_to_test_Is[I0]))


        # self.dh.data = {'y': yy_Is, 'x': xx_Is
        # xoi0 = np.linspace(np.min(self.lats), np.max(self.lats), 50)
        # yoi0 = np.linspace(np.min(self.lons), np.max(self.lons), 50)
        # gridppOI.optimal_interpolation(

        # Histogram plot
        # y, x = np.histogram(self.values[Is[I1]], bins=self.edges)
        # self.ds4.data = {'x': self.values[Is[I0]], 'y':  self.elevs[Is[I0]]}
        # self.ds4.data = {'top': y + y0, 'bottom':  0 * y, 'left': self.edges[:-1], 'right': self.edges[1:]}
        # self.ds3.data = {'x': self.values[Is[I1]], 'y':  self.elevs[Is[I]]}

        self.set_apply_button()
        self.old_flags = copy.deepcopy(flags)
        self.number_tests = self.number_tests + 1
        
    def set_dataset(self, index: int, datetime: int):
        unixtime = titantuner.date_to_unixtime(datetime // 100) + datetime % 100 * 3600
        keys = [self.source.keys[index]]
        index = int(index)
        self.dataset_index = index
        if self.source.requires_time:
            keys += [unixtime]

        """ What to do if a dataset cannot be loaded? E.g. if it has corrupt data

        Here we just create an empty dataset. Another option would be to remove the dataset from the
        list of available datasets.
        """
        try:
            self.dataset = self.source.load(*keys)
        except titantuner.InvalidDatasetException as e:
            self.dataset = titantuner.dataset.Dataset("Invalid", [], [], [], [], 0, "")
            print(e)

        self.old_flags = None
        self.lats = self.dataset.lats
        self.lons = self.dataset.lons
        self.elevs = self.dataset.elevs
        self.values = self.dataset.values
        self.variable = self.dataset.variable
        if self.variable == "ta":
            self.units = "C"
        elif self.variable == "rr":
            self.units = "mm/h"
        else:
            self.units = "C"
            # raise NotImplementedError

    def set_background(self, value):
        tile_provider = get_provider(value)
        # Replace the tile renderer
        found = None
        for i, r in enumerate(self.p.renderers):
            if isinstance(r, TileRenderer):
                found = i
        if found is not None:
            self.p.renderers[found] = TileRenderer(tile_source=tile_provider)

    def lat2y(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        return np.log(np.tan(math.pi / 4 + np.radians(a) / 2)) * RADIUS

    def lon2x(self, a):
        RADIUS = 6378137.0 # in meters on the equator
        return np.radians(a) * RADIUS
    
dico_combine_test_code2ui = {"single": "Apply test (no combinaison / first test)",
                                "combineOK_if_1_OK": "Combine: pass if pass this test or previous, reject others", # softer test
                                "combineOK_if_both_OK": "Combine: pass if pass both this test and previous, reject others", # harder test
                                "combineBad_if_1_Bad": "Combine: reject if flagged by this test or previous, keep others", # harder test
                                "combineBad_if_both_Bad": "Combine: reject if flagged both by this test and previous, keep others", # softer test
                                "chain": "Combine test: further test only unflagged values"}
dico_combine_test_ui2code =  {v: k for k, v in dico_combine_test_code2ui.items()}

