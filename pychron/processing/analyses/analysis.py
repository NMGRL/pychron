#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Int, Str, Float, Dict, Property, \
    Date, Any
#============= standard library imports ========================
import time
from datetime import datetime
from uncertainties import ufloat
from collections import namedtuple
#============= local library imports  ==========================
from pychron.helpers.isotope_utils import extract_mass
from pychron.processing.analyses.analysis_view import DBAnalysisView, AnalysisView
from pychron.processing.arar_age import ArArAge
from pychron.processing.analyses.summary import AnalysisSummary
from pychron.processing.analyses.db_summary import DBAnalysisSummary
from pychron.experiment.utilities.identifier import make_runid, make_aliquot_step
from pychron.processing.isotope import Isotope, Blank, Baseline, Sniff
from pychron.pychron_constants import ARGON_KEYS
from pychron.helpers.formatting import calc_percent_error

Fit = namedtuple('Fit', 'fit filter_outliers filter_outlier_iterations filter_outlier_std_devs')


class Analysis(ArArAge):
    analysis_summary_klass = AnalysisSummary
    analysis_summary = Instance(AnalysisSummary)
    analysis_view_klass = AnalysisView
    analysis_view = Instance(AnalysisView)

    labnumber = Str
    aliquot = Int
    step = Str

    aliquot_step_str = Str

    omit_ideo = False
    omit_spec = False
    omit_iso = False

    def flush(self, *args, **kw):
        '''
        '''
        return

    def commit(self, *args, **kw):
        '''
        '''
        return

    def sync(self, obj, **kw):
        self._sync(obj, **kw)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

    def _sync(self, *args, **kw):
        '''
        '''
        return

    def _analysis_summary_default(self):
        return self.analysis_summary_klass(model=self)

    def _analysis_view_default(self):
        v = self.analysis_view_klass()
        self._sync_view(v)
        return v

    def _sync_view(self, v):
        pass


class DBAnalysis(Analysis):
    analysis_summary_klass = DBAnalysisSummary
    analysis_view_klass = DBAnalysisView
    #     status = Int
    temp_status = Int
    record_id = Str
    uuid = Str

    persisted_age = None

    sample = Str
    material = Str
    project = Str
    comment = Str
    mass_spectrometer = Str
    extract_device = Str
    position = Str
    extract_value = Float
    extract_units = Str
    cleanup_duration = Float
    extract_duration = Float
    analysis_type = Str
    tag = Str
    timestamp = Float
    rundate = Date

    peak_center = Any

    ic_factors = Dict

    group_id = Int
    graph_id = Int

    status_text = Property
    age_string = Property

    def set_temporary_ic_factor(self, k, v, e):
        iso = self.get_isotope(detector=k)
        if iso:
            iso.temporary_ic_factor = (v, e)

    def set_temporary_blank(self, k, v, e):
        if self.isotopes.has_key(k):
            iso = self.isotopes[k]
            iso.temporary_blank = Blank(value=v, error=e)

    def get_baseline_corrected_signal_dict(self):
        get = lambda iso: iso.baseline_corrected_value()
        return self._get_isotope_dict(get)

    def get_baseline_dict(self):
        get = lambda iso: iso.baseline.uvalue
        return self._get_isotope_dict(get)

    def get_ic_factor(self, det):
        if det in self.ic_factors:
            r = self.ic_factors[det]
        else:
            #get the ic_factor from preferences if available otherwise 1.0
            r = ArArAge.get_ic_factor(self, det)

        return r

    def get_db_fit(self, meas_analysis, name, kind):
        try:
            sel_hist = meas_analysis.selected_histories
            sel_fithist = sel_hist.selected_fits
            fits = sel_fithist.fits
            return next((fi for fi in fits
                         if fi.isotope.kind == kind and \
                            fi.isotope.molecular_weight.name == name
                        ), None)

        except AttributeError:
            pass

    def set_tag(self, tag):

        name = tag.name
        self.tag = name

        omit = name == 'omit'
        for a in ('ideo', 'spec', 'iso'):
            a = 'omit_{}'.format(a)
            v = getattr(tag, a)
            setattr(self, a, v)
            if v:
                omit = True

        self.temp_status = 1 if omit else 0

    def init(self, meas_analysis):
        pass

    def sync_irradiation(self, ln):
        """
            copy irradiation info starting with a labnumber dbrecord
        """
        self._sync_irradiation(ln)


    def sync_arar(self, meas_analysis):
        self.debug('not using db arar')
        return

        hist = meas_analysis.selected_histories.selected_arar
        if hist:
            result = hist.arar_result
            self.persisted_age = ufloat(result.age, result.age_err)
            self.age = self.persisted_age / self.arar_constants.age_scalar

            attrs = ['k39', 'ca37', 'cl36',
                     'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36', 'rad40']
            d = dict()
            f = lambda k: getattr(result, k)
            for ai in attrs:
                vs = map(f, (ai, '{}_err'.format(ai)))
                d[ai] = ufloat(*vs)

            d['age_err_wo_j'] = result.age_err_wo_j
            self.arar_result.update(d)

    def _sync(self, meas_analysis, unpack=False):
        '''
            copy values from meas_AnalysisTable
            and other associated tables
        '''
        # copy meas_analysis attrs
        nocast = lambda x: x
        attrs = [
            ('labnumber', 'labnumber', lambda x: x.identifier),
            ('aliquot', 'aliquot', int),
            ('step', 'step', str),
            #                  ('status', 'status', int),
            ('comment', 'comment', str),
            ('uuid', 'uuid', str),
            ('rundate', 'analysis_timestamp', nocast),
            ('timestamp', 'analysis_timestamp',
             lambda x: time.mktime(x.timetuple())
            ),
        ]
        for key, attr, cast in attrs:
            v = getattr(meas_analysis, attr)
            setattr(self, key, cast(v))

        self.record_id = make_runid(self.labnumber, self.aliquot, self.step)

        tag = meas_analysis.tag
        if tag:
            tag = meas_analysis.tag_item
            self.set_tag(tag)

        #self.tag = tag or ''
        #if self.tag:
        #    self.temp_status = 1

        # copy related table attrs
        self._sync_irradiation(meas_analysis.labnumber)
        self._sync_isotopes(meas_analysis, unpack)
        self._sync_detector_info(meas_analysis)
        self._sync_extraction(meas_analysis)
        self._sync_analysis_info(meas_analysis)

        self.analysis_type = self._get_analysis_type(meas_analysis)

    def _sync_irradiation(self, ln):
        """
            copy irradiation info starting with a labnumber dbrecord
        """
        self._sync_j(ln)
        pos = ln.irradiation_position
        if pos:
            level = pos.level
            irrad = level.irradiation

            self.irradiation_pos = str(pos.position)
            self.irradiation_level = level.name
            self.irradiation = irrad.name

            self._sync_chron_segments(irrad)
            self._sync_production_ratios(irrad)
            self._sync_interference_corrections(irrad)

    def _sync_j(self, ln):
        s, e = 1, 0
        if ln.selected_flux_history:
            f = ln.selected_flux_history.flux
            s = f.j
            e = f.j_err

        self.j = ufloat(s, e)

    def _sync_production_ratios(self, irradiation):
        pr = irradiation.production
        cak, clk = pr.Ca_K, pr.Cl_K

        self.production_ratios = dict(Ca_K=cak, Cl_K=clk)

    def _sync_chron_segments(self, irradiation):
        chron = irradiation.chronology

        convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)
        if chron:
            doses = chron.get_doses()
            analts = self.timestamp
            if isinstance(analts, float):
                analts = datetime.fromtimestamp(analts)

            segments = []
            for st, en in doses:
                if st is not None and en is not None:
                    dur = en - st
                    dt = analts - st
                    #                             dt = 45
                    segments.append((1, convert_days(dur), convert_days(dt)))

            decay_time = 0
            d_o = doses[0][0]
            it = 0
            if d_o is not None:
                it = time.mktime(d_o.timetuple())

                #decay_time = convert_days(analts - d_o)

            #self.decay_time=decay_time
            self.irradiation_time = it
            self.chron_segments = segments

    def _sync_interference_corrections(self, irradiation):
        pr = irradiation.production
        prs = dict()
        for pk in ['K4039', 'K3839', 'K3739', 'Ca3937', 'Ca3837', 'Ca3637', 'Cl3638']:
            v, e = getattr(pr, pk), getattr(pr, '{}_err'.format(pk))
            if v is None:
                v = 0
            if e is None:
                e = 0

            prs[pk.lower()] = ufloat(v, e)

        self.interference_corrections = prs

    def _sync_extraction(self, meas_analysis):
        extraction = meas_analysis.extraction
        if extraction:
            self.extract_device = self._get_extraction_device(extraction)
            self.extract_value = extraction.extract_value

            # add extract units to meas_ExtractionTable
            #             eu = extraction.extract_units or 'W'
            #             self.extract_units = eu
            self.extract_units = 'W'

            self.cleanup = extraction.cleanup_duration
            self.duration = extraction.extract_duration
            self.position = self._get_position(extraction)

    def _sync_view(self, av=None):
        if av is None:
            av = self.analysis_view

        av.analysis_type = self.analysis_type
        av.analysis_id = self.record_id
        av.load(self)

    def _sync_analysis_info(self, meas_analysis):
        self.sample = self._get_sample(meas_analysis)
        self.material = self._get_material(meas_analysis)
        self.project = self._get_project(meas_analysis)
        self.mass_spectrometer = self._get_mass_spectrometer(meas_analysis)

    def _sync_detector_info(self, meas_analysis):

        #disc_idx=['Ar36','Ar37','Ar38','Ar39','Ar40']

        #discrimination saved as 1amu disc not 4amu
        discriminations = self._get_discriminations(meas_analysis)

        self.ic_factors = self._get_ic_factors(meas_analysis)
        for iso in self.isotopes.itervalues():
            det = iso.detector
            iso.ic_factor = self.get_ic_factor(det)

            idisc = ufloat(1, 1e-20)
            if iso.detector in discriminations:
                mass = extract_mass(iso.name)

                disc, refmass = discriminations[det]
                ni = mass - round(refmass)

                mass = iso.mass
                n = mass - refmass
                #self.info('{} {} {}'.format(iso.name, n, ni))
                #calculate discrimination
                idisc = disc ** n

                #e=disc
                #for i in range(int(ni)-1):
                #    e*=disc
                #
                #idisc=ufloat(idisc.nominal_value, e.std_dev)

            iso.discrimination = idisc


    def _sync_isotopes(self, meas_analysis, unpack):
        #self.isotopes=timethis(self._get_isotopes, args=(meas_analysis,),
        #kwargs={'unpack':True},msg='sync-isotopes')
        self.isotopes = self._get_isotopes(meas_analysis,
                                           unpack=unpack)
        self.isotope_fits = self._get_isotope_fits()

        self.peak_center = self._get_peak_center(meas_analysis)


    def _get_isotope_dict(self, get):
        d = dict()
        for ki in ARGON_KEYS:
            if self.isotopes.has_key(ki):
                v = get(self.isotopes[ki])
            else:
                v = ufloat(0, 0)
            d[ki] = v

        return d

    def _get_ic_factors(self, meas_analysis):
        icfs = dict()
        if meas_analysis.selected_histories:
            hist = meas_analysis.selected_histories.selected_detector_intercalibration
            if hist:
                for ic in hist.detector_intercalibrations:
                    icfs[ic.detector.name] = ufloat(ic.user_value, ic.user_error)

        return icfs

    def _get_position(self, extraction):
        r = ''
        pos = extraction.positions

        pp = []
        for pi in pos:
            pii = pi.position

            if pii:
                pp.append(pii)
            else:
                ppp = []
                x, y, z = pi.x, pi.y, pi.z
                if x is not None and y is not None:
                    ppp.append(x)
                    ppp.append(y)
                if z is not None:
                    ppp.append(z)

                if ppp:
                    pp.append('({})'.format(','.join(ppp)))

        if pp:
            r = ','.join(map(str, pp))

        return r

    def _get_baselines(self, isotopes, meas_analysis, unpack):
        for dbiso in meas_analysis.isotopes:
            if not dbiso.molecular_weight:
                continue

            name = dbiso.molecular_weight.name
            if not name in isotopes:
                continue

            det = dbiso.detector.name

            iso = isotopes[name]

            kw = dict(
                dbrecord=dbiso,
                name=name,
                detector=det,
                unpack=unpack)

            if dbiso.kind == 'baseline':
                result = None
                if dbiso.results:
                    result = dbiso.results[-1]

                r = Baseline(dbresult=result,
                             **kw)
                fit = self.get_db_fit(meas_analysis, name, 'baseline')
                if fit is None:
                    fit = Fit(fit='average_sem',
                              filter_outliers=False,
                              filter_outlier_iterations=0,
                              filter_outlier_std_devs=0)

                r.set_fit(fit)
                iso.baseline = r

            elif dbiso.kind == 'sniff':
                r = Sniff(**kw)
                iso.sniff = r

    def _get_isotope_fits(self):
        keys = self.isotope_keys
        fs = [self.isotopes[ki].fit
              for ki in keys]
        return fs

    def _get_isotopes(self, meas_analysis, unpack):
        isotopes = dict()
        self._get_signals(isotopes, meas_analysis, unpack)
        self._get_baselines(isotopes, meas_analysis, unpack)
        self._get_blanks(isotopes, meas_analysis)

        return isotopes

    def _get_blanks(self, isodict, meas_analysis):
        history = meas_analysis.selected_histories.selected_blanks
        keys = isodict.keys()
        if history:
            for ba in history.blanks:
                isok = ba.isotope
                if isok in keys:
                    blank = isodict[isok].blank
                    blank.set_uvalue((ba.user_value,
                                      ba.user_error))
                    blank.fit = ba.fit or ''
                    keys.remove(isok)
                    if not keys:
                        break

    def _get_signals(self, isodict, meas_analysis, unpack):
        for iso in meas_analysis.isotopes:
            if not iso.kind == 'signal' or not iso.molecular_weight:
                continue

            name = iso.molecular_weight.name
            if name not in isodict:
                if not iso.detector:
                    return

                det = iso.detector.name
                result = None

                if iso.results:
                    result = iso.results[-1]

                r = Isotope(
                    mass=iso.molecular_weight.mass,
                    dbrecord=iso,
                    dbresult=result,
                    name=name,
                    detector=det,
                    unpack=unpack)

                if r.unpack_error:
                    self.warning('Bad isotope {} {}. error: {}'.format(self.record_id, name, r.unpack_error))
                    self.temp_status = 1
                else:
                    fit = self.get_db_fit(meas_analysis, name, 'signal')

                    if fit is None:
                        fit = Fit(fit='linear', filter_outliers=False,
                                  filter_outlier_iterations=1,
                                  filter_outlier_std_devs=2)
                    r.set_fit(fit)
                    isodict[name] = r

    def _get_peak_center(self, meas_analysis):
        return ufloat(0, 0)

    def _get_extraction_device(self, extraction):
        r = ''
        if extraction.extraction_device:
            r = extraction.extraction_device.name
        return r

    def _get_analysis_type(self, meas_analysis):
        r = ''
        if meas_analysis:
            r = meas_analysis.measurement.analysis_type.name
        return r

    def _get_mass_spectrometer(self, meas_analysis):
        return meas_analysis.measurement.mass_spectrometer.name.lower()

    def _get_discriminations(self, meas_analysis):
        """
            discriminations should be saved as 1amu not 4amu
        """
        selected_hist = meas_analysis.selected_histories.selected_detector_param
        d = dict()
        if selected_hist:
            for dp in selected_hist.detector_params:
                d[dp.detector.name] = (ufloat(dp.disc, dp.disc_error), dp.refmass)
                #d[dp.detector.name] = (ufloat(1.004, 0.000145), dp.refmass)
                #dp=selected_hist.detector_param
                #return ufloat(dp.disc, dp.disc_error)
        return d

    def _get_sample(self, meas_analysis):
        ln = meas_analysis.labnumber
        r = ''
        if ln.sample:
            r = ln.sample.name
        return r

    def _get_material(self, meas_analysis):
        m = ''
        ln = meas_analysis.labnumber
        if ln.sample and ln.sample.material:
            m = ln.sample.material.name
        return m

    def _get_project(self, meas_analysis):
        ln = meas_analysis.labnumber
        sample = ln.sample
        r = ''
        if sample and sample.project:
            r = sample.project.name
        return r

    def _get_rundate(self, meas_analysis):
        if meas_analysis.analysis_timestamp:
            date = meas_analysis.analysis_timestamp.date()
            return date.strftime('%Y-%m-%d')

    def _get_runtime(self, meas_analysis):
        if meas_analysis.analysis_timestamp:
            ti = meas_analysis.analysis_timestamp.time()
            return ti.strftime('%H:%M:%S')

    def _get_age_string(self):

        a = self.age
        e = self.age_err_wo_j

        pe = calc_percent_error(a, e)

        return u'{:0.3f} +/-{:0.3f} ({}%)'.format(a, e, pe)

    def _get_status_text(self):
        r = 'OK'

        if self.temp_status != 0:
            r = 'Omitted'

        return r

        #def __getattr__(self, attr):
        #    lattr = attr.lower()
        #    #         print attr, ISOREGEX.match(attr)
        #    #         if ISOREGEX.match(attr):
        #    if '/' in attr:
        #        #treat as ratio
        #        n, d = attr.split('/')
        #        return getattr(self, n) / getattr(self, d)
        #
        #    if lattr in ('ar40', 'ar39', 'ar38', 'ar37', 'ar36'):
        #        return getattr(self, attr.capitalize())
        #
        #    if ISOREGEX.match(attr):
        #        if attr in self.isotopes:
        #            return self.isotopes[attr].uvalue
        #
        #    self.debug('no attribute {}'.format(attr))
        #    raise AttributeError


if __name__ == '__main__':
    pass
    #============= EOF =============================================
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