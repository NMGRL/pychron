# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================

from traits.api import Instance, Int, Str, Bool, \
    Event, Property, Float, Date

# ============= standard library imports ========================
from collections import namedtuple
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import format_percent_error, floatfmt
from pychron.core.helpers.logger_setup import new_logger
from pychron.processing.arar_age import ArArAge
# from pychron.processing.analyses.analysis_view import AnalysisView
#from pychron.processing.analyses.summary import AnalysisSummary
#from pychron.processing.analyses.db_summary import DBAnalysisSummary
from pychron.experiment.utilities.identifier import make_aliquot_step, make_runid
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import PLUSMINUS

Fit = namedtuple('Fit', 'fit '
                        'filter_outliers filter_outlier_iterations filter_outlier_std_devs '
                        'error_type include_baseline_error, time_zero_offset')

logger = new_logger('Analysis')


class Analysis(ArArAge):
    group_id = Int
    graph_id = Int

    analysis_view_klass = ('pychron.processing.analyses.analysis_view','AnalysisView')
    analysis_view = Instance('pychron.processing.analyses.analysis_view.AnalysisView')

    labnumber = Str
    aliquot = Int
    step = Str
    aliquot_step_str = Str
    sample = Str
    material = Str
    project = Str
    comment = Str
    mass_spectrometer = Str
    analysis_type = Str
    extract_value = Float
    extract_units = Str
    cleanup_duration = Float
    extract_duration = Float
    extract_device = Str
    position = Str
    rundate = Date

    is_plateau_step = False
    temp_status = Int
    value_filter_omit = Bool
    table_filter_omit = Bool
    tag = Str
    data_reduction_tag = Str

    record_id = Property(depends_on='labnumber,aliquot, step')
    status_text = Property
    age_string = Property

    omit_ideo = False
    omit_spec = False
    omit_iso = False
    omit_series = False

    has_raw_data = False
    has_changes = False

    recall_event = Event
    tag_event = Event
    invalid_event = Event

    def trigger_recall(self):
        self.recall_event = self

    def trigger_tag(self, analyses=None):
        if analyses is None:
            analyses = [self, ]

        self.tag_event = analyses

    def trigger_invalid(self, analyses=None):
        if analyses is None:
            analyses = [self, ]
        self.invalid_event = analyses

    def is_temp_omitted(self, include_value_filtered=True):
        return self.temp_status or self.table_filter_omit or self.value_filter_omit if include_value_filtered else False

    def is_tag_omitted(self, omit_key):
        if omit_key:
            return getattr(self, omit_key)

    def is_omitted(self, omit_key=None, include_value_filtered=True):
        omit = False
        if omit_key:
            omit = getattr(self, omit_key)
            #print ai.aliquot, r, omit, ai.filter_omit
        #return r or ai.filter_omit #or ai.tag == 'omit'
        #omit=False
        return self.is_temp_omitted(include_value_filtered) or omit

    def flush(self, *args, **kw):
        """
        """
        return

    def commit(self, *args, **kw):
        """
        """
        return

    def sync(self, obj, **kw):
        self._sync(obj, **kw)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

    def _sync(self, *args, **kw):
        """
        """
        return

    # def _analysis_summary_default(self):
    #     return self.analysis_summary_klass(model=self)

    def _analysis_view_default(self):

        mod, klass= self.analysis_view_klass
        mod = __import__(mod, fromlist=[klass,])
        klass=getattr(mod, klass)
        # v = self.analysis_view_klass()
        v = klass()
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

    def _get_record_id(self):
        return make_runid(self.labnumber, self.aliquot, self.step)

    def _get_age_string(self):
        a = self.age
        e = self.age_err
        pe = format_percent_error(a, e)

        return u'{} +/-{} ({}%)'.format(floatfmt(a), floatfmt(e), pe)

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

    def _get_status_text(self):
        r = 'OK'

        if self.is_omitted():
            # if self.temp_status != 0 or self.filter_omit:
            r = 'Omitted'

        return r

    #mirror labnumber
    @property
    def identifier(self):
        return self.labnumber


if __name__ == '__main__':
    pass
    # ============= EOF =============================================
    #def _sync_irradiation(self, meas_analysis):
    #    ln = meas_analysis.labnumber
    #    self.irradiation_info = self._get_irradiation_info(ln)
    #
    #    dbpos = ln.irradiation_position
    #    if dbpos:
    #        pos = dbpos.position
    #        irrad = dbpos.level.irradiation.name
    #        level = dbpos.level.name
    #        self.irradiation_str = '{} {}{}'.format(irrad, level, pos)
    #
    #    self.j = self._get_j(ln)
    #    self.production_ratios = self._get_production_ratios(ln)

    #    def _load_timestamp(self, ln):
    #        ts = self.timestamp
    #        if not ts:
    #            ts = ArArAge._load_timestamp(self, ln)
    #        return ts
    #
    #
    #    def _get_j(self, ln):
    #        s, e = 1, 0
    #        if ln.selected_flux_history:
    #            f = ln.selected_flux_history.flux
    #            s = f.j
    #            e = f.j_err
    #        return ufloat(s, e)
    #
    #    def _get_production_ratios(self, ln):
    #        lev = self._get_irradiation_level(ln)
    #        cak = 1
    #        clk = 1
    #        if lev:
    #            ir = lev.irradiation
    #            pr = ir.production
    #            cak, clk = pr.Ca_K, pr.Cl_K
    #
    #        return dict(Ca_K=cak, Cl_K=clk)
    #
    #    def _get_irradiation_level(self, ln):
    #        if ln:
    #            pos = ln.irradiation_position
    #            if pos:
    #                self.irradiation_pos = str(pos.position)
    #                return pos.level
    #
    #
    #    def _get_irradiation_info(self, ln):
    #        '''
    #            return k4039, k3839,k3739, ca3937, ca3837, ca3637, cl3638, chronsegments, decay_time
    #        '''
    #        prs = (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), [], 1
    #        irradiation_level = self._get_irradiation_level(ln)
    #        if irradiation_level:
    #            irradiation = irradiation_level.irradiation
    #            if irradiation:
    #                self.irradiation = irradiation.name
    #                self.irradiation_level = irradiation_level.name
    #
    #                pr = irradiation.production
    #                if pr:
    #                    prs = []
    #                    for pi in ['K4039', 'K3839', 'K3739', 'Ca3937', 'Ca3837', 'Ca3637', 'Cl3638']:
    #                        v, e = getattr(pr, pi), getattr(pr, '{}_err'.format(pi))
    #                        prs.append((v if v is not None else 1, e if e is not None else 0))
    #
    #                        #                    prs = [(getattr(pr, pi), getattr(pr, '{}_err'.format(pi)))
    #                        #                           for pi in ['K4039', 'K3839', 'K3739', 'Ca3937', 'Ca3837', 'Ca3637', 'Cl3638']]
    #
    #                chron = irradiation.chronology
    #                #                def convert_datetime(x):
    #                #                    try:
    #                #                        return datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    #                #                    except ValueError:
    #                #                        pass
    #                #                convert_datetime = lambda x:datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    #
    #                convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)
    #                if chron:
    #                    doses = chron.get_doses()
    #                    #                    chronblob = chron.chronology
    #                    #
    #                    #                    doses = chronblob.split('$')
    #                    #                    doses = [di.strip().split('%') for di in doses]
    #                    #
    #                    #                    doses = [map(convert_datetime, d) for d in doses if d]
    #
    #                    analts = self.timestamp
    #                    #                     print analts
    #                    if isinstance(analts, float):
    #                        analts = datetime.fromtimestamp(analts)
    #
    #                    segments = []
    #                    for st, en in doses:
    #                        if st is not None and en is not None:
    #                            dur = en - st
    #                            dt = analts - st
    #                            #                             dt = 45
    #                            segments.append((1, convert_days(dur), convert_days(dt)))
    #                            #                             segments.append((1, convert_days(dur), dt))
    #
    #                    decay_time = 0
    #                    d_o = doses[0][0]
    #                    if d_o is not None:
    #                        decay_time = convert_days(analts - d_o)
    #
    #                    #                    segments = [(1, convert_days(ti)) for ti in durs]
    #                    prs.append(segments)
    #                    prs.append(decay_time)
    #                    #                     prs.append(45)
    #
    #                    #         print 'aasfaf', ln, prs
    #
    #        return prs