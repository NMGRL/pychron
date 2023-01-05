# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from collections import namedtuple
from math import ceil
from operator import attrgetter

import six
from numpy import Inf, polyfit, polyval, arange, argmin
from pyface.message_dialog import information
from pyface.qt import QtCore
from traits.api import Event, Dict, List, Str
from traits.has_traits import HasTraits
from traitsui.handler import Handler
from uncertainties import ufloat, std_dev, nominal_value

from pychron.core.helpers.fits import convert_fit
from pychron.core.helpers.formatting import format_percent_error, floatfmt
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.helpers.logger_setup import new_logger
from pychron.core.regression.ols_regressor import PolynomialRegressor
from pychron.envisage.view_util import open_view
from pychron.experiment.utilities.runid import make_runid, make_aliquot_step
from pychron.processing.arar_age import ArArAge
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import PLUSMINUS, NULL_STR, AR_AR, EXCLUDE_TAGS

Fit = namedtuple(
    "Fit",
    "fit "
    "filter_outliers filter_outlier_iterations filter_outlier_std_devs "
    "error_type include_baseline_error, time_zero_offset",
)

logger = new_logger("Analysis")


def min_max(a, b, vs):
    return min(a, vs.min()), max(b, vs.max())


OX = 50
OY = 50
XOFFSET = 25
YOFFSET = 25
WINDOW_CNT = 0


class CloseHandler(Handler):
    def closed(self, info, is_ok):
        global WINDOW_CNT
        WINDOW_CNT -= 1
        WINDOW_CNT = max(0, WINDOW_CNT)

    def init(self, info):
        global WINDOW_CNT
        WINDOW_CNT += 1
        info.ui.control.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)


def show_inspection_factory(record_id, isotopes):
    from pychron.graph.stacked_graph import StackedGraph

    def calculate(dxs, dys, fit):
        reg = PolynomialRegressor(xs=dxs, ys=dys)
        reg.fit = fit
        ts = arange(4, len(dxs), 10)
        ys, iys = [], []
        for ti in ts:
            reg.set_truncate(str(ti))
            reg.calculate()
            ys.append(reg.predict_error(0))
            iys.append(reg.predict(0))

        return ts, ys, iys

    iso = isotopes[0]
    dxs, dys = iso.offset_xs, iso.ys

    g = StackedGraph()

    g.new_plot(show_legend="ur")
    g.new_plot()

    g.set_y_title("Intercept Error %", plotid=0)
    g.set_y_title("T-zero Intensity", plotid=1)

    xs, ys, iys = calculate(dxs, dys, "linear")
    lmin, lidx = min(ys), argmin(ys)

    g.new_series(xs, ys, plotid=0)
    g.new_series(xs, iys, plotid=1)
    g.set_series_label("Linear", plotid=0)

    xs, ys, iys = calculate(dxs, dys, "parabolic")
    pmin, pidx = min(ys), argmin(ys)

    g.new_series(xs, ys, plotid=0)
    g.new_series(xs, iys, plotid=1)
    g.set_series_label("Parabolic", plotid=0)

    # g.add_vertical_rule(lidx, plotid=0, color='black')
    # g.add_vertical_rule(pidx, plotid=0, color='green')

    g.set_y_limits(min_=0, plotid=0)
    g.window_title = "{} Inspection".format(make_title(record_id, isotopes))
    return g


def show_residuals_factory(record_id, isotopes):
    from pychron.graph.residuals_graph import ResidualsGraph

    iso = isotopes[0]

    g = ResidualsGraph()
    g.new_plot(padding_right=75, padding_left=100)
    g.set_x_title("Time (s)")
    g.set_y_title("Intensity ({})".format(iso.units))

    if iso.fit is None:
        iso.fit = "linear"

    xs, ys = iso.get_data()
    g.new_series(
        xs,
        ys,
        fit=iso.efit,
        truncate=iso.truncate,
        filter_outliers_dict=iso.filter_outliers_dict,
        color="black",
    )
    g.set_regressor(iso.regressor, 0)
    g.set_x_limits(min_=0, pad="0.1", pad_style="upper")
    g.set_y_limits(pad="0.1")
    g.refresh()

    g.window_title = "{} Residuals".format(make_title(record_id, isotopes))
    return g


def show_evolutions_factory(
    record_id,
    isotopes,
    show_evo=True,
    show_equilibration=False,
    show_baseline=False,
    show_statistics=False,
    ncols=1,
    scale_to_equilibration=False,
    **kw
):
    from pychron.graph.stacked_regression_graph import (
        ColumnStackedRegressionGraph,
        StackedRegressionGraph,
    )

    if WINDOW_CNT > 20:
        information(
            None,
            "You have too many Isotope Evolution windows open. Close some before proceeding",
        )
        return

    if ncols > 1:
        isotopes = sort_isotopes(isotopes, reverse=True, key=attrgetter("name"))

        def reorder(l, n):
            l = [l[i : i + n] for i in range(0, len(l), n)]
            nl = []
            for ri in range(len(l[0])):
                for col in l:
                    try:
                        nl.append(col[ri])
                    except IndexError:
                        pass
            return nl

        nrows = ceil(len(isotopes) / ncols)
        isotopes = reorder(isotopes, nrows)
        g = ColumnStackedRegressionGraph(
            resizable=True,
            ncols=ncols,
            nrows=nrows,
            container_dict={
                "padding_top": 15 * nrows,
                "spacing": (0, 15),
                "padding_bottom": 40,
            },
            show_grouping=True,
        )
        resizable = "hv"
    else:
        resizable = "h"
        isotopes = sort_isotopes(isotopes, reverse=False, key=attrgetter("name"))
        g = StackedRegressionGraph(
            resizable=True, container_dict={"spacing": 15}, show_grouping=True
        )

    args = (
        g,
        isotopes,
        resizable,
        show_evo,
        show_equilibration,
        show_baseline,
        show_statistics,
        scale_to_equilibration,
    )

    def update_grouping(n):
        for iso in isotopes:
            iso.set_grouping(n)

        make_graph(*args)

    g.on_trait_change(update_grouping, "grouping")
    # g.plotcontainer.spacing = 10
    g.window_height = min(275 * len(isotopes), 800)
    g.window_x = OX + XOFFSET * WINDOW_CNT
    g.window_y = OY + YOFFSET * WINDOW_CNT

    make_graph(*args)

    g.window_title = make_title(record_id, isotopes)

    return g


def make_title(record_id, isotopes):
    return "{} {}".format(record_id, ",".join([i.name for i in reversed(isotopes)]))


def make_graph(
    g,
    isotopes,
    resizable,
    show_evo=True,
    show_equilibration=False,
    show_baseline=False,
    show_statistics=False,
    scale_to_equilibration=False,
):
    g.clear()

    if not show_evo:
        xmi = Inf
        xma = -Inf
    else:
        xmi, xma = 0, -Inf

    for i, iso in enumerate(isotopes):
        ymi, yma = Inf, -Inf

        p = g.new_plot(padding=[80, 10, 10, 40], resizable=resizable)
        g.add_limit_tool(p, "x")
        g.add_limit_tool(p, "y")
        g.add_axis_tool(p, p.x_axis)
        g.add_axis_tool(p, p.y_axis)
        if show_statistics:
            g.add_statistics(i)

        p.y_axis.title_spacing = 50
        if show_equilibration:
            sniff = iso.sniff
            if sniff.xs.shape[0]:
                g.new_series(
                    sniff.offset_xs, sniff.ys, type="scatter", fit=None, color="red"
                )
                ymi, yma = min_max(ymi, yma, sniff.ys)
                xmi, xma = min_max(xmi, xma, sniff.offset_xs)

        if show_evo:
            if iso.fit is None:
                iso.fit = "linear"

            xs, ys = iso.get_data()
            g.new_series(
                xs,
                ys,
                fit=iso.efit,
                truncate=iso.truncate,
                filter_outliers_dict=iso.filter_outliers_dict,
                color="black",
            )
            g.set_regressor(iso.regressor, i)

            xmi, xma = min_max(xmi, xma, iso.offset_xs)
            if not scale_to_equilibration:
                ymi, yma = min_max(ymi, yma, iso.ys)

        if show_baseline:
            baseline = iso.baseline
            g.new_series(
                baseline.offset_xs,
                baseline.ys,
                type="scatter",
                fit=baseline.efit,
                filter_outliers_dict=baseline.filter_outliers_dict,
                color="blue",
            )
            xmi, xma = min_max(xmi, xma, baseline.offset_xs)
            if not scale_to_equilibration:
                ymi, yma = min_max(ymi, yma, baseline.ys)

        xpad = "0.025,0.05"
        ypad = "0.05"
        if scale_to_equilibration:
            ypad = None
            r = (yma - ymi) * 0.02
            # ymi = yma - r

            fit = iso.fit
            if fit != "average":
                fit, _ = convert_fit(iso.fit)
                fy = polyval(polyfit(iso.offset_xs, iso.ys, fit), 0)
                if ymi > fy:
                    ymi = fy - r

                fy = polyval(polyfit(iso.offset_xs, iso.ys, fit), xma)
                if fy > yma:
                    yma = fy
                elif fy < ymi:
                    ymi = fy - r

            # yma += r

        g.set_x_limits(min_=xmi, max_=xma, pad=xpad)
        g.set_y_limits(min_=ymi, max_=yma, pad=ypad, plotid=i)

        g.set_x_title("Time (s)", plotid=i)
        g.set_y_title("{} ({})".format(iso.name, iso.units), plotid=i)

    g.refresh()


class IdeogramPlotable(HasTraits):
    history_id = 0
    group_id = 0
    graph_id = 0
    aux_id = 0
    tab_id = 0
    group = ""
    aux_name = ""

    _label_name = None

    tag = "ok"
    tag_note = ""
    uage = None
    temp_status = Str("ok")
    otemp_status = None
    _record_id = None
    temp_selected = False
    comment = ""
    j = None
    labnumber = ""
    aliquot = 0
    step = ""
    timestamp = 0
    uuid = None

    def __init__(self, make_arar_constants=True, *args, **kw):
        super(IdeogramPlotable, self).__init__(*args, **kw)
        if make_arar_constants:
            self.arar_constants = ArArConstants()

    def baseline_corrected_intercepts_to_dict(self):
        pass

    def blanks_to_dict(self):
        pass

    def icfactors_to_dict(self):
        pass

    def interference_corrected_values_to_dict(self):
        pass

    def ic_corrected_values_to_dict(self):
        pass

    def decay_corrected_values_to_dict(self):
        pass

    def refresh_view(self):
        pass

    def is_omitted(self, tags=None, omit_by_tag=True):
        ret = False
        # if omit_by_tag and not self.otemp_status is not None:
        if omit_by_tag and self.otemp_status is None:
            # if otemp_status is not None then user toggled this point and we are no longer going to respect the tag
            # omission
            ret = self.is_omitted_by_tag(tags)

        return ret or self.temp_selected

    def is_omitted_by_tag(self, tags=None):
        if tags is None:
            tags = EXCLUDE_TAGS
        return self.tag in tags

    def set_temp_status(self, tag):

        tag = tag.lower()
        if tag != "ok":
            self.otemp_status = tag
        else:
            self.otemp_status = "omit"

        self.temp_status = tag

    def set_tag(self, tag):
        if isinstance(tag, dict):
            self.tag_note = tag.get("note", "")
            self.tag = tag.get("name", "")
            self.subgroup = tag.get("subgroup", "")
        else:
            self.tag = tag

        self.temp_status = self.tag

    def value_string(self, t):
        a, e = self._value_string(t)
        pe = format_percent_error(a, e)
        return "{} {}{} ({}%)".format(floatfmt(a), PLUSMINUS, floatfmt(e), pe)

    @property
    def display_uuid(self):
        u = self.uuid
        if not u:
            u = ""
        return u[:8]

    @property
    def label_name(self):
        n = self._label_name
        if n is None:
            n = "{:02n}".format(self.aliquot)

        return n

    @label_name.setter
    def label_name(self, v):
        self._label_name = v

    @property
    def status_text(self):
        return self.temp_status.lower()

    @property
    def identifier_aliquot_pair(self):
        return "{}-{}".format(self.identifier, self.aliquot)

    @property
    def identifier(self):
        return self.labnumber

    @identifier.setter
    def identifier(self, v):
        self.labnumber = v

    @property
    def record_id(self):
        v = self._record_id
        if v is None:
            v = make_runid(self.labnumber, self.aliquot, self.step)
        return v

    @record_id.setter
    def record_id(self, v):
        self._record_id = v

    @property
    def temp_selected(self):
        return self.temp_status in EXCLUDE_TAGS

    def _value_string(self, t):
        raise NotImplementedError


class Analysis(ArArAge, IdeogramPlotable):
    analysis_view_klass = (
        "pychron.processing.analyses.view.analysis_view",
        "AnalysisView",
    )
    _analysis_view = (
        None  # Instance('pychron.processing.analyses.analysis_view.AnalysisView')
    )

    # sample
    sample = ""
    material = ""
    grainsize = ""
    project = ""
    principal_investigator = ""
    elevation = 0
    igsn = ""
    lithology = ""
    lithology_type = ""
    lithology_group = ""
    lithology_class = ""
    latitude = 0
    longitude = 0
    reference = ""
    rlocation = ""
    mask_position = ""
    mask_name = ""
    reprate = ""
    sample_prep_comment = ""
    sample_note = ""

    # collection
    experiment_type = AR_AR
    acquisition_software = None
    data_reduction_software = None
    laboratory = ""
    instrument_name = ""
    analystName = ""
    measured_response_stream = None
    requested_output_stream = None
    setpoint_stream = None
    load_name = ""
    load_holder = ""
    light_value = ""

    experiment_queue_name = ""

    # environmentals
    lab_temperature = 0
    lab_humidity = 0
    lab_airpressure = 0

    increment = None
    aliquot_step_str = ""
    mass_spectrometer = ""
    analysis_type = ""
    extract_value = 0
    extract_units = ""
    cleanup_duration = 0
    pre_cleanup_duration = 0
    post_cleanup_duration = 0
    cryo_temperature = 0
    extract_duration = 0
    extract_device = ""
    position = ""
    experiment_txt = ""
    extraction_script_blob = ""
    measurement_script_blob = ""
    snapshots = List
    extraction_script_name = ""
    measurement_script_name = ""
    xyz_position = ""
    collection_time_zero_offset = 0
    beam_diameter = 0
    pattern = ""
    ramp_duration = 0
    ramp_rate = 0
    peak_center = 0
    peak_center_data = None
    peak_center_reference_detector = None
    additional_peak_center_data = None
    peak_center_interpolation_kind = None
    peak_center_use_interpolation = False
    peak_center_reference_isotope = None
    collection_version = ""
    source_parameters = Dict
    filament_parameters = Dict
    deflections = Dict
    gains = Dict
    repository_identifier = ""
    flux_history = ""

    admit_delay = 0
    # processing
    is_plateau_step = False
    # temp_status = Int(0)
    # temp_status = 'ok'
    # otemp_status = None
    # value_filter_omit = False
    # table_filter_omit = False
    # tag = ''
    data_reduction_tag = ""
    branch = NULL_STR

    # status_text = Property
    # age_string = Property

    # omit_ideo = False
    # omit_spec = False
    # omit_iso = False
    # omit_series = False

    blank_changes = List
    fit_changes = List

    # meta
    has_raw_data = False
    has_changes = False

    recall_event = Event
    tag_event = Event
    invalid_event = Event
    omit_event = Event

    monitor_name = None
    monitor_age = None
    monitor_material = None

    _extraction_type = None

    @property
    def extraction_type(self):
        if self._extraction_type:
            return self._extraction_type

        if self.step:
            return "Incremental Heating"
        else:
            return "Laser Fusion"

    @extraction_type.setter
    def extraction_type(self, v):
        self._extraction_type = v

    def get_baseline_corrected_signal_dict(self):
        get = lambda iso: iso.get_baseline_corrected_value()
        return self._get_isotope_dict(get)

    def get_baseline_dict(self):
        get = lambda iso: iso.baseline.uvalue
        return self._get_isotope_dict(get)

    def get_ic_factor(self, det):
        # iso = next((i for i in self.isotopes.values() if i.detector == det), None)
        iso = self.get_isotope(detector=det)
        if iso:
            r = iso.ic_factor
        else:
            r = ufloat(1, 0)

        return r

    def get_isotope_evolutions(self, isotopes=None, load_data=True, **kw):
        if isotopes:
            if isinstance(isotopes[0], (str, six.text_type)):
                nisotopes = []
                for i in isotopes:
                    try:
                        iso = self.isotopes[i]
                    except KeyError:
                        iso = next(
                            (
                                ii.baseline
                                for ii in self.isotopes.values()
                                if ii.detector == i
                            ),
                            None,
                        )
                    if iso:
                        nisotopes.append(iso)
                isotopes = nisotopes
        else:
            isotopes = list(self.isotopes.values())

        if load_data:
            keys = ["{}{}".format(k.name, k.detector) for k in isotopes]
            self.load_raw_data(keys=keys)

        if kw.get("show_inspection"):
            return show_inspection_factory(self.record_id, isotopes)
        elif kw.get("show_residuals"):
            return show_residuals_factory(self.record_id, isotopes)
        else:
            return show_evolutions_factory(self.record_id, isotopes, **kw)

    def show_isotope_evolutions(self, *args, **kw):
        g = self.get_isotope_evolutions(*args, **kw)
        if g:
            open_view(g, handler=CloseHandler())
            return g

    def trigger_recall(self, analyses=None):
        if analyses is None:
            analyses = [
                self,
            ]

        self.recall_event = analyses

    def trigger_tag(self, analyses=None):
        if analyses is None:
            analyses = [
                self,
            ]

        self.tag_event = analyses

    def trigger_invalid(self, analyses=None):
        if analyses is None:
            analyses = [
                self,
            ]
        self.invalid_event = analyses

    def trigger_omit(self, analyses=None):
        if analyses is None:
            analyses = [
                self,
            ]
        self.omit_event = analyses

    def sync(self, obj, **kw):
        self._sync(obj, **kw)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

    def _sync(self, *args, **kw):
        """ """
        return

    def refresh_view(self):
        if self._analysis_view:
            self._sync_view(self._analysis_view)

    @property
    def analysis_view(self):
        v = self._analysis_view
        if v is None:
            v = self.analysis_view_factory()

        return v

    def analysis_view_factory(self, quick=False):
        mod, klass = self.analysis_view_klass
        mod = __import__(
            mod,
            fromlist=[
                klass,
            ],
        )
        klass = getattr(mod, klass)
        # v = self.analysis_view_klass()
        v = klass()
        self._analysis_view = v
        self._sync_view(v, quick=quick)
        return v

    def sync_view(self, **kw):
        self._sync_view(**kw)

    def _sync_view(self, av=None, quick=False, **kw):
        if av is None:
            av = self.analysis_view
        try:
            av.load(self, quick=quick)
        except BaseException as e:
            import traceback

            traceback.print_exc()
            print("sync view {}".format(e))

    @property
    def age_string(self):
        a = self.age
        e = self.age_err
        pe = format_percent_error(a, e)

        return "{} {}{} ({}%)".format(floatfmt(a), PLUSMINUS, floatfmt(e), pe)

    def _value_string(self, t):
        if t == "uF":
            a, e = self.f, self.f_err
        elif t == "uage":
            a, e = nominal_value(self.uage), std_dev(self.uage)
        else:
            v = self.get_value(t)
            if isinstance(v, Isotope):
                v = v.get_intensity()
            a, e = nominal_value(v), std_dev(v)

        return a, e

    def _get_isotope_dict(self, get):
        d = dict()
        for ki, v in self.isotopes.items():
            d[ki] = (v.detector, get(v))

        return d

    def __str__(self):
        return "{}<{}>".format(self.record_id, self.__class__.__name__)


# ============= EOF =============================================
