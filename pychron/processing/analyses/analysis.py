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

from numpy import Inf
from pyface.message_dialog import information
from pyface.qt import QtCore
from traits.api import Event, Dict, List
from traits.has_traits import HasTraits
from traitsui.handler import Handler
from uncertainties import ufloat

from pychron.core.helpers.formatting import format_percent_error, floatfmt
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.helpers.logger_setup import new_logger
from pychron.envisage.view_util import open_view
from pychron.experiment.utilities.identifier import make_runid, make_aliquot_step
from pychron.processing.arar_age import ArArAge
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import PLUSMINUS, NULL_STR

Fit = namedtuple('Fit', 'fit '
                        'filter_outliers filter_outlier_iterations filter_outlier_std_devs '
                        'error_type include_baseline_error, time_zero_offset')

logger = new_logger('Analysis')


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


def show_evolutions_factory(record_id, isotopes, show_evo=True, show_equilibration=False, show_baseline=False):
    if WINDOW_CNT > 20:
        information(None, 'You have too many Isotope Evolution windows open. Close some before proceeding')
        return

    from pychron.graph.stacked_regression_graph import StackedRegressionGraph

    if not show_evo:
        xmi = Inf
        xma = -Inf
    else:
        xmi, xma = 0, -Inf

    g = StackedRegressionGraph(resizable=True)
    g.plotcontainer.spacing = 10
    g.window_height = min(275 * len(isotopes), 800)
    g.window_x = OX + XOFFSET * WINDOW_CNT
    g.window_y = OY + YOFFSET * WINDOW_CNT

    isotopes = sort_isotopes(isotopes, reverse=False, key=lambda x: x.name)

    for i, iso in enumerate(isotopes):
        ymi, yma = Inf, -Inf

        p = g.new_plot(padding=[80, 10, 10, 40])
        g.add_limit_tool(p, 'x')
        g.add_limit_tool(p, 'y')
        g.add_axis_tool(p, p.x_axis)
        g.add_axis_tool(p, p.y_axis)

        p.y_axis.title_spacing = 50
        if show_equilibration:
            sniff = iso.sniff
            g.new_series(sniff.xs, sniff.ys,
                         type='scatter',
                         fit=None,
                         color='red')
            ymi, yma = min_max(ymi, yma, sniff.ys)
            xmi, xma = min_max(xmi, xma, sniff.xs)

        if show_evo:
            if iso.fit is None:
                iso.fit = 'linear'

            g.new_series(iso.xs, iso.ys,
                         fit=iso.fit,
                         filter_outliers_dict=iso.filter_outliers_dict,
                         color='black')
            ymi, yma = min_max(ymi, yma, iso.ys)
            xmi, xma = min_max(xmi, xma, iso.xs)

        if show_baseline:
            baseline = iso.baseline
            g.new_series(baseline.xs, baseline.ys,
                         type='scatter', fit=baseline.fit,
                         filter_outliers_dict=baseline.filter_outliers_dict,
                         color='blue')
            ymi, yma = min_max(ymi, yma, baseline.ys)
            xmi, xma = min_max(xmi, xma, baseline.xs)

        g.set_x_limits(min_=xmi, max_=xma, pad='0.025,0.05')
        g.set_y_limits(min_=ymi, max_=yma, pad='0.05', plotid=i)
        g.set_x_title('Time (s)', plotid=i)
        g.set_y_title('{} (fA)'.format(iso.name), plotid=i)

    g.refresh()
    g.window_title = '{} {}'.format(record_id, ','.join([i.name for i in reversed(isotopes)]))

    return g


class IdeogramPlotable(HasTraits):
    group_id = 0
    graph_id = 0

    tag = 'ok'
    uage = None
    temp_status = 'ok'
    otemp_status = None
    record_id = ''
    temp_selected = False
    comment = ''
    j = None

    def __init__(self, *args, **kw):
        super(IdeogramPlotable, self).__init__(*args, **kw)
        self.arar_constants = ArArConstants()

    def is_omitted(self):
        return self.is_omitted_by_tag() or self.temp_selected

    def is_omitted_by_tag(self, tags=None):
        if tags is None:
            tags = ('omit', 'invalid', 'outlier')
        return self.tag in tags

    def set_temp_status(self, tag):
        tag = tag.lower()
        if tag != 'ok':
            self.otemp_status = tag
        else:
            self.otemp_status = 'omit'

        self.temp_status = tag

    def set_tag(self, tag):
        self.tag = tag


class Analysis(ArArAge, IdeogramPlotable):
    analysis_view_klass = ('pychron.processing.analyses.view.analysis_view', 'AnalysisView')
    _analysis_view = None  # Instance('pychron.processing.analyses.analysis_view.AnalysisView')

    # ids
    # record_id = Property(depends_on='labnumber,aliquot, step')
    _record_id = None
    group_id = 0  # Int
    graph_id = 0  # Int

    # sample
    sample = ''
    material = ''
    project = ''
    latitude = 0
    longitude = 0
    elevation = 0
    igsn = ''

    # collection
    acquisition_software = None
    data_reduction_software = None
    laboratory = ''
    analystName = ''
    uuid = None  # Str
    labnumber = ''
    aliquot = 0
    step = ''
    increment = None
    aliquot_step_str = ''
    mass_spectrometer = ''
    analysis_type = ''
    extract_value = 0
    extract_units = ''
    cleanup_duration = 0
    extract_duration = 0
    extract_device = ''
    position = ''
    experiment_txt = ''
    extraction_script_blob = ''
    measurement_script_blob = ''
    snapshots = List
    extraction_script_name = ''
    measurement_script_name = ''
    xyz_position = ''
    collection_time_zero_offset = 0
    beam_diameter = 0
    pattern = ''
    ramp_duration = 0
    ramp_rate = 0
    peak_center = 0
    peak_center_data = None
    additional_peak_center_data = None
    collection_version = ''
    source_parameters = Dict
    deflections = Dict
    gains = Dict
    repository_identifier = ''

    # processing
    is_plateau_step = False
    # temp_status = Int(0)
    # temp_status = 'ok'
    # otemp_status = None
    # value_filter_omit = False
    # table_filter_omit = False
    # tag = ''
    data_reduction_tag = ''
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

    standard_name = None
    standard_age = None
    standard_material = None

    _experiment_type = None

    @property
    def experiment_type(self):
        if self._experiment_type:
            return self._experiment_type

        if self.step:
            return 'Incremental Heating'
        else:
            return 'Laser Fusion'

    @experiment_type.setter
    def experiment_type(self, v):
        self._experiment_type = v

    def get_baseline_corrected_signal_dict(self):
        get = lambda iso: iso.get_baseline_corrected_value()
        return self._get_isotope_dict(get)

    def get_baseline_dict(self):
        get = lambda iso: iso.baseline.uvalue
        return self._get_isotope_dict(get)

    def get_ic_factor(self, det):
        iso = next((i for i in self.isotopes.itervalues() if i.detector == det), None)
        if iso:
            r = iso.ic_factor
        else:
            r = ufloat(1, 0)

        return r

    def show_isotope_evolutions(self, isotopes=None, **kw):
        if isotopes:
            if isinstance(isotopes[0], (str, unicode)):
                nisotopes = []
                for i in isotopes:
                    try:
                        iso = self.isotopes[i]
                    except KeyError:
                        iso = next((ii.baseline for ii in self.isotopes.itervalues() if ii.detector == i), None)
                    if iso:
                        nisotopes.append(iso)
                isotopes = nisotopes
                # isotopes = [self.isotopes[i] for i in isotopes]
        else:
            isotopes = self.isotopes.values()

        keys = ['{}{}'.format(k.name, k.detector) for k in isotopes]

        self.load_raw_data(keys=keys)
        g = show_evolutions_factory(self.record_id, isotopes, **kw)
        if g:
            open_view(g, handler=CloseHandler())

            return g

    def trigger_recall(self, analyses=None):
        if analyses is None:
            analyses = [self, ]

        self.recall_event = analyses

    def trigger_tag(self, analyses=None):
        if analyses is None:
            analyses = [self, ]

        self.tag_event = analyses

    def trigger_invalid(self, analyses=None):
        if analyses is None:
            analyses = [self, ]
        self.invalid_event = analyses

    def trigger_omit(self, analyses=None):
        if analyses is None:
            analyses = [self, ]
        self.omit_event = analyses

    def sync(self, obj, **kw):
        self._sync(obj, **kw)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

    def _sync(self, *args, **kw):
        """
        """
        return

    def refresh_view(self):
        if self._analysis_view:
            self._sync_view(self._analysis_view)

    @property
    def analysis_view(self):
        print 'call analyis va'
        v = self._analysis_view
        if v is None:
            mod, klass = self.analysis_view_klass
            mod = __import__(mod, fromlist=[klass, ])
            klass = getattr(mod, klass)
            # v = self.analysis_view_klass()
            v = klass()
            self._analysis_view = v
        self._sync_view(v)

        return v

    def sync_view(self, **kw):
        self._sync_view(**kw)

    def _sync_view(self, av=None, **kw):
        if av is None:
            av = self.analysis_view
        try:
            av.load(self)
        except BaseException, e:
            import traceback

            traceback.print_exc()
            print 'sync view {}'.format(e)

    def value_string(self, t):
        if t == 'uF':
            a, e = self.F, self.F_err
        elif t == 'uage':
            a, e = self.uage.nominal_value, self.uage.std_dev
        else:
            v = self.get_value(t)
            if isinstance(v, Isotope):
                v = v.get_intensity()
            a, e = v.nominal_value, v.std_dev
        pe = format_percent_error(a, e)
        return u'{} {}{} ({}%)'.format(floatfmt(a), PLUSMINUS, floatfmt(e), pe)

    @property
    def age_string(self):
        a = self.age
        e = self.age_err
        pe = format_percent_error(a, e)

        return u'{} {}{} ({}%)'.format(floatfmt(a), PLUSMINUS, floatfmt(e), pe)

    @property
    def status_text(self):
        return self.temp_status.lower()

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
        return self.temp_status in ('omit', 'outlier', 'invalid')

    def _get_isotope_dict(self, get):
        d = dict()
        for ki, v in self.isotopes.iteritems():
            d[ki] = (v.detector, get(v))

        return d

    def __str__(self):
        return '{}<{}>'.format(self.record_id, self.__class__.__name__)
# ============= EOF =============================================
