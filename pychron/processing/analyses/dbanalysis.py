from datetime import datetime
import struct
import time

from traits.trait_types import Str, Float, Either, Date, Any, Dict, List
from uncertainties import ufloat

from pychron.processing.analyses.analysis import Analysis, Fit
from pychron.processing.analyses.analysis_view import DBAnalysisView
from pychron.processing.analyses.changes import BlankChange, FitChange
from pychron.processing.isotope import Blank, Baseline, Sniff, Isotope


__author__ = 'ross'


class DBAnalysis(Analysis):
    #analysis_summary_klass = DBAnalysisSummary
    analysis_view_klass = DBAnalysisView
    #     status = Int

    # record_id = Str
    uuid = Str

    persisted_age = None

    sample = Str
    material = Str
    project = Str
    comment = Str
    mass_spectrometer = Str

    experiment_txt = Str

    #extraction
    extract_device = Str
    position = Str
    extract_value = Float
    extract_units = Str
    cleanup_duration = Float
    extract_duration = Float

    beam_diameter = Either(Float, Str)
    pattern = Str
    mask_position = Either(Float, Str)
    mask_name = Str
    attenuator = Either(Float, Str)
    ramp_duration = Either(Float, Str)
    ramp_rate = Either(Float, Str)
    reprate = Either(Float, Str)

    analysis_type = Str

    timestamp = Float
    rundate = Date

    peak_center = Float
    peak_center_data = Any

    ic_factors = Dict

    blank_changes = List
    fit_changes = List


    def set_temporary_ic_factor(self, k, v, e):
        iso = self.get_isotope(detector=k)
        if iso:
            iso.temporary_ic_factor = (v, e)

    def set_temporary_blank(self, k, v, e):
        if self.isotopes.has_key(k):
            iso = self.isotopes[k]
            iso.temporary_blank = Blank(value=v, error=e)

    def get_baseline_corrected_signal_dict(self):
        get = lambda iso: iso.get_baseline_corrected_value()
        return self._get_isotope_dict(get)

    def get_baseline_dict(self):
        get = lambda iso: iso.baseline.uvalue
        return self._get_isotope_dict(get)

    def get_ic_factor(self, det):
        if det in self.ic_factors:
            r = self.ic_factors[det]
        else:
            r = ufloat(1, 1e-20)
            #get the ic_factor from preferences if available otherwise 1.0
            # storing ic_factor in preferences causing issues
            # ic_factor stored in detectors.cfg
            # r = ArArAge.get_ic_factor(self, det)

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

        except AttributeError, e:
            print e

    def set_tag(self, tag):
        if isinstance(tag, str):
            self.tag = tag
            omit = tag == 'invalid'
        else:
            name = tag.name
            self.tag = name

            omit = name == 'omit'
            for a in ('ideo', 'spec', 'iso', 'series'):
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

    def sync_detector_info(self, meas_analysis, **kw):
        self._sync_detector_info(meas_analysis, **kw)

    # def sync_arar(self, meas_analysis):
    #     # self.debug('not using db arar')
    #     return
    #
    #     hist = meas_analysis.selected_histories.selected_arar
    #     if hist:
    #         result = hist.arar_result
    #         self.persisted_age = ufloat(result.age, result.age_err)
    #         self.age = self.persisted_age / self.arar_constants.age_scalar
    #
    #         attrs = ['k39', 'ca37', 'cl36',
    #                  'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36', 'rad40']
    #         d = dict()
    #         f = lambda k: getattr(result, k)
    #         for ai in attrs:
    #             vs = map(f, (ai, '{}_err'.format(ai)))
    #             d[ai] = ufloat(*vs)
    #
    #         d['age_err_wo_j'] = result.age_err_wo_j
    #         self.arar_result.update(d)

    def _sync(self, meas_analysis, unpack=True, load_changes=False):
        """
            copy values from meas_AnalysisTable
            and other associated tables
        """

        self._sync_meas_analysis_attributes(meas_analysis)
        self._sync_analysis_info(meas_analysis)

        # copy related table attrs
        self._sync_experiment(meas_analysis)
        self._sync_irradiation(meas_analysis.labnumber)

        #this is the dominant time sink
        self._sync_isotopes(meas_analysis, unpack)

        self._sync_detector_info(meas_analysis)
        self._sync_extraction(meas_analysis)

        if load_changes:
            self._sync_changes(meas_analysis)

        self.analysis_type = self._get_analysis_type(meas_analysis)

    def _sync_meas_analysis_attributes(self, meas_analysis):
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

        # self.record_id = make_runid(self.labnumber, self.aliquot, self.step)

        tag = meas_analysis.tag
        if tag:
            tag = meas_analysis.tag_item
            self.set_tag(tag)

    def _sync_changes(self, meas_analysis):

        self.blank_changes = [BlankChange(bi) for bi in meas_analysis.blanks_histories]
        self.fit_changes = [FitChange(fi) for fi in meas_analysis.fit_histories]

    def _sync_experiment(self, meas_analysis):
        ext = meas_analysis.extraction
        exp = ext.experiment
        if exp:
            self.experiment_txt = exp.blob

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
            self._sync_production_ratios(level)
            self._sync_interference_corrections(level)

            self.production_name = level.production.name

    def _sync_j(self, ln):
        s, e = 1, 0
        if ln.selected_flux_history:
            f = ln.selected_flux_history.flux
            s = f.j
            e = f.j_err

        self.j = ufloat(s, e)

    def _sync_production_ratios(self, level):
        pr = level.production
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
            for pwr, st, en in doses:
                if st is not None and en is not None:
                    dur = en - st
                    dt = analts - st
                    segments.append((pwr, convert_days(dur), convert_days(dt)))

            d_o = doses[0][1]
            it = 0
            if d_o is not None:
                it = time.mktime(d_o.timetuple())

            self.irradiation_time = it
            self.chron_segments = segments
            self.chron_dosages = chron.get_doses()

    def _sync_interference_corrections(self, level):
        pr = level.production
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
            #sensitivity
            shist = meas_analysis.selected_histories.selected_sensitivity
            if shist:
                sm = extraction.sensitivity_multiplier or 1
                s = shist.sensitivity.value
                self.sensitivity = sm * s

            self.extract_device = self._get_extraction_device(extraction)
            self.extract_value = extraction.extract_value

            # add extract units to meas_ExtractionTable
            #             eu = extraction.extract_units or 'W'
            #             self.extract_units = eu
            self.extract_units = 'W'

            self.cleanup = extraction.cleanup_duration
            self.duration = extraction.extract_duration
            self.position = self._get_position(extraction)

            for attr in ('beam_diameter', 'pattern',
                         'ramp_rate', 'ramp_duration'):
                v = getattr(extraction, attr)
                if v is None:
                    v = ''
                setattr(self, attr, v)

            #uv
            for attr in ('reprate', 'mask_position', 'mask_name', 'attenuator'):
                v = getattr(extraction, attr)
                if v is None:
                    v = ''
                setattr(self, attr, v)

    def _sync_view(self, av=None):
        if av is None:
            av = self.analysis_view
        av.load(self)

    def _sync_analysis_info(self, meas_analysis):
        self.sample = self._get_sample(meas_analysis)
        self.material = self._get_material(meas_analysis)
        self.project = self._get_project(meas_analysis)
        self.mass_spectrometer = self._get_mass_spectrometer(meas_analysis)

    def _sync_detector_info(self, meas_analysis, **kw):

        #disc_idx=['Ar36','Ar37','Ar38','Ar39','Ar40']

        #discrimination saved as 1amu disc not 4amu
        discriminations = self._get_discriminations(meas_analysis)

        self.ic_factors = self._get_ic_factors(meas_analysis)
        for iso in self.isotopes.itervalues():
            det = iso.detector
            iso.ic_factor = self.get_ic_factor(det)

            idisc = ufloat(1, 1e-20)
            if iso.detector in discriminations:
                disc, refmass = discriminations[det]
                # ni = mass - round(refmass)

                mass = iso.mass
                n = mass - refmass
                #self.info('{} {} {}'.format(iso.name, n, ni))
                #calculate discrimination
                idisc = disc ** n
                e = disc
                #for i in range(int(ni)-1):
                #    e*=disc
                #
                idisc = ufloat(idisc.nominal_value, e.std_dev)

            iso.discrimination = idisc

    def _sync_isotopes(self, meas_analysis, unpack):
        #self.isotopes=timethis(self._get_isotopes, args=(meas_analysis,),
        #kwargs={'unpack':True},msg='sync-isotopes')
        self.isotopes = self._get_isotopes(meas_analysis,
                                           unpack=unpack)
        self.isotope_fits = self._get_isotope_fits()

        pc, data = self._get_peak_center(meas_analysis)
        self.peak_center = pc
        self.peak_center_data = data

    def _get_isotope_dict(self, get):
        d = dict()
        for ki, v in self.isotopes.iteritems():
            d[ki] = get(v)

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

            kw = dict(dbrecord=dbiso,
                      name=name,
                      detector=det,
                      unpack=unpack)

            if dbiso.kind == 'baseline':
                result = None
                if dbiso.results:
                    result = dbiso.results[-1]
                r = Baseline(dbresult=result, **kw)
                fit = self.get_db_fit(meas_analysis, name, 'baseline')
                if fit is None:
                    fit = Fit(fit='average',
                              error_type='SEM',
                              filter_outliers=False,
                              filter_outlier_iterations=0,
                              filter_outlier_std_devs=0,
                              include_baseline_error=False)

                r.set_fit(fit, notify=False)
                iso.baseline = r

            elif dbiso.kind == 'sniff':
                r = Sniff(**kw)
                iso.sniff = r

    def _get_isotope_fits(self):
        keys = self.isotope_keys
        fs = [(self.isotopes[ki].fit,
               self.isotopes[ki].error_type,
               self.isotopes[ki].filter_outliers_dict)
              for ki in keys]
        bs = [(self.isotopes[ki].baseline.fit,
               self.isotopes[ki].baseline.error_type,
               self.isotopes[ki].baseline.filter_outliers_dict)
              for ki in keys]

        return fs + bs

    def _get_isotopes(self, meas_analysis, unpack):
        isotopes = dict()
        self._get_signals(isotopes, meas_analysis, unpack)
        self._get_baselines(isotopes, meas_analysis, unpack)
        self._get_blanks(isotopes, meas_analysis)

        return isotopes

    def _get_blanks(self, isodict, meas_analysis):
        if meas_analysis.selected_histories:
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
            if name in isodict:
                continue

            if not iso.detector:
                continue

            det = iso.detector.name
            result = None

            if iso.results:
                result = iso.results[-1]

            r = Isotope(mass=iso.molecular_weight.mass,
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
                    fit = Fit(fit='linear',
                              error_type='SEM',
                              filter_outliers=False,
                              filter_outlier_iterations=1,
                              filter_outlier_std_devs=2,
                              include_baseline_error=False)
                r.set_fit(fit, notify=False)
                isodict[name] = r

    def _get_peak_center(self, meas_analysis):

        pc = meas_analysis.peak_center
        if pc:
            center = float(pc.center)
            packed_xy = pc.points
            return center, zip(*[struct.unpack('<ff', packed_xy[i:i + 8])
                                 for i in xrange(0, len(packed_xy), 8)])
        else:
            return 0.0, None

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
                self.discrimination = disc = ufloat(dp.disc, dp.disc_error)
                d[dp.detector.name] = (disc, dp.refmass)
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

    def _post_process_msg(self, msg):
        msg = '{} {}'.format(self.record_id, msg)
        return msg