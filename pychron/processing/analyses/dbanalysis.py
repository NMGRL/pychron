# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.trait_types import Str, Float, Either, Date, Any, Dict, List, Long
# ============= standard library imports ========================
import os
from datetime import datetime
from itertools import izip
import struct
import time
from uncertainties import ufloat
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import remove_extension
from pychron.database.orms.isotope.meas import meas_AnalysisTable
from pychron.processing.analyses.analysis import Analysis, Fit
from pychron.processing.analyses.analysis_view import DBAnalysisView
from pychron.processing.analyses.changes import BlankChange, FitChange
from pychron.processing.analyses.exceptions import NoProductionError
from pychron.processing.analyses.view.snapshot_view import Snapshot
from pychron.processing.isotope import Blank, Baseline, Sniff, Isotope
from pychron.pychron_constants import INTERFERENCE_KEYS


def get_xyz_position(extraction):
    def g():
        for pp in extraction.positions:
            x, y, z = pp.x, pp.y, pp.z
            if x is not None and y is not None:
                if z is not None:
                    rr = '{:0.3f},{:0.3f},{:0.3f}'.format(x, y, z)
                else:
                    rr = '{:0.3f},{:0.3f}'.format(x, y)
                yield rr

    return ';'.join(list(g()))


def get_position(extraction):
    def g():
        for pi in extraction.positions:
            pii = pi.position
            if pii:
                yield str(pii)

    return ','.join(list(g()))


class DBAnalysis(Analysis):
    meas_analysis_id = Long
    analysis_view_klass = DBAnalysisView

    uuid = Str

    persisted_age = None

    experiment_txt = Str

    xyz_position = Str
    snapshots = List

    beam_diameter = Either(Float, Str)
    pattern = Str
    mask_position = Either(Float, Str)
    mask_name = Str
    attenuator = Either(Float, Str)
    ramp_duration = Either(Float, Str)
    ramp_rate = Either(Float, Str)
    reprate = Either(Float, Str)

    timestamp = Float
    rundate = Date

    collection_time_zero_offset = Float

    peak_center = Float
    peak_center_data = Any

    ic_factors = Dict

    blank_changes = List
    fit_changes = List

    extraction_script_name = Str
    measurement_script_name = Str
    extraction_script_blob = Str
    measurement_script_blob = Str

    selected_blanks_id = Long

    def set_ic_factor(self, det, v, e):
        for iso in self.get_isotopes(det):
            iso.ic_factor = ufloat(v, e)

    def set_temporary_ic_factor(self, k, v, e):
        iso = self.get_isotope(detector=k)
        if iso:
            iso.temporary_ic_factor = (v, e)

    def set_temporary_blank(self, k, v, e):
        self.debug('setting temporary blank iso={}, v={}, e={}'.format(k, v, e))
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
        iso = next((i for i in self.isotopes.itervalues() if i.detector == det), None)
        if iso:
            r = iso.ic_factor
        else:
            r = ufloat(1, 0)

        # if det in self.ic_factors:
        #     r = self.ic_factors[det]
        # else:
        #     r = ufloat(1, 1e-20)

        return r

    def get_db_fit(self, meas_analysis, name, kind, selected_histories):
        try:
            if selected_histories is None:
                selected_histories = meas_analysis.selected_histories

            sel_fithist = selected_histories.selected_fits
            fits = sel_fithist.fits
            return next((fi for fi in fits
                         if fi.isotope.kind == kind and \
                         fi.isotope.molecular_weight.name == name), None)

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
    def sync_aux(self, dbrecord_tuple, load_changes=True):
        if isinstance(dbrecord_tuple, meas_AnalysisTable):
            meas_analysis = dbrecord_tuple
        else:
            args = izip(*dbrecord_tuple)
            meas_analysis = args.next()[0]

        if load_changes:
            self._sync_changes(meas_analysis)

        self._sync_experiment(meas_analysis)
        self._sync_script_blobs(meas_analysis)
        self.has_changes = True

    def _sync(self, dbrecord_tuple, unpack=True, load_aux=False):
        """
            copy values from meas_AnalysisTable
            and other associated tables
        """

        ms, ls, isos, samples, projects, materials = izip(*dbrecord_tuple)
        meas_analysis = ms[0]
        lab = ls[0]

        sample = samples[0]
        project = projects[0]
        material = materials[0]
        if sample:
            self.sample = sample
            self.project = project
            if material:
                self.material = material

        # print 'pre maa'
        self._sync_meas_analysis_attributes(meas_analysis)

        # print 'pre irrad'
        self._sync_irradiation(lab)

        # print 'pre dr'
        # sync the dr tag first so we can set selected_histories
        sh = self._sync_data_reduction_tag(meas_analysis)
        # print 'pre isotopes'
        #this is the dominant time sink
        self._sync_isotopes(meas_analysis, isos,
                            unpack, load_peak_center=load_aux, selected_histories=sh)
        # timethis(self._sync_isotopes, args=(meas_analysis, isos, unpack),
        #          kwargs={'load_peak_center': load_aux})

        # print 'pre det info'
        self._sync_detector_info(meas_analysis)
        if load_aux:
            self.sync_aux(meas_analysis)

        # print 'pre ext'
        self._sync_extraction(meas_analysis)
        # print 'pre meas'
        self._sync_measurement(meas_analysis)

    def _sync_data_reduction_tag(self, meas_analysis):
        tag = meas_analysis.data_reduction_tag
        if tag:
            self.data_reduction_tag = tag.name

            #get the data_reduction_tag_set entry associated with this analysis
            drentry = next((ai for ai in tag.analyses if ai.analysis_id == meas_analysis.id), None)
            print drentry.selected_histories
            return drentry.selected_histories

    def _sync_script_blobs(self, meas_analysis):
        meas = meas_analysis.measurement
        if meas:
            script = meas.script
            if script:
                self.measurement_script_blob = script.blob

        ext = meas_analysis.extraction
        if ext:
            script = ext.script
            if script:
                self.extraction_script_blob = script.blob

    def _sync_extraction(self, meas_analysis):
        extraction = meas_analysis.extraction
        if extraction:
            if extraction.script:
                self.extraction_script_name = remove_extension(extraction.script.name)

            # sensitivity
            if meas_analysis.selected_histories:
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
            self.position = get_position(extraction)
            self.xyz_position = get_xyz_position(extraction)

            for attr in ('beam_diameter', 'pattern',
                         'ramp_rate', 'ramp_duration'):
                v = getattr(extraction, attr)
                if v is None:
                    v = ''
                setattr(self, attr, v)

            # uv
            if 'uv' in self.extract_device:
                for attr in ('reprate', 'mask_position', 'mask_name', 'attenuator'):
                    v = getattr(extraction, attr)
                    if v is None:
                        v = ''
                    setattr(self, attr, v)

            snapshots = extraction.snapshots
            if snapshots:
                self.snapshots = [Snapshot(path=si.path,
                                           name=os.path.basename(si.path),
                                           remote_path=si.remote_path,
                                           image=si.image) for si in snapshots]

    def _sync_measurement(self, meas_analysis):
        if meas_analysis:
            meas = meas_analysis.measurement
            if meas:
                if meas.script:
                    self.measurement_script_name = remove_extension(meas.script.name)

                self.analysis_type = meas.analysis_type.name
                self.mass_spectrometer = meas.mass_spectrometer.name.lower()
                self.collection_time_zero_offset = meas.time_zero_offset or 0

    def _sync_meas_analysis_attributes(self, meas_analysis):
        # copy meas_analysis attrs
        nocast = lambda x: x

        attrs = [
            ('labnumber', 'labnumber', lambda x: x.identifier),
            ('aliquot', 'aliquot', int),
            ('step', 'step', str),
            ('comment', 'comment', str),
            ('uuid', 'uuid', str),
            ('meas_analysis_id', 'id', nocast),
            ('rundate', 'analysis_timestamp', nocast),
            ('analysis_timestamp', 'analysis_timestamp', nocast),
            ('timestamp', 'analysis_timestamp',
             lambda x: time.mktime(x.timetuple()))]
        for key, attr, cast in attrs:
            v = getattr(meas_analysis, attr)
            setattr(self, key, cast(v))

        tag = meas_analysis.tag
        if tag:
            tag = meas_analysis.tag_item
            self.set_tag(tag)

    def _sync_changes(self, meas_analysis):
        bid = None
        if meas_analysis.selected_histories:
            bid = meas_analysis.selected_histories.selected_blanks_id

        self.blank_changes = [BlankChange(bi, active=bi.id == bid) for bi in meas_analysis.blanks_histories]
        self.fit_changes = [FitChange(fi) for fi in meas_analysis.fit_histories]

        if bid is not None:
            self.selected_blanks_id = bid

    def _sync_experiment(self, meas_analysis):
        ext = meas_analysis.extraction
        if ext:
            exp = ext.experiment
            self.debug('syncing experiment, {}'.format(exp))
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

        self.j = ufloat(s, e, tag='J')

    def _sync_production_ratios(self, level):
        pr = level.production
        if pr:
            cak, clk = (pr.Ca_K, pr.Ca_K_err), (pr.Cl_K, pr.Cl_K_err)
            self.production_ratios = dict(Ca_K=ufloat(*cak),
                                          Cl_K=ufloat(*clk))
        else:
            raise NoProductionError()

    def _sync_chron_segments(self, irradiation):
        chron = irradiation.chronology
        if chron:
            analts = self.timestamp
            if isinstance(analts, float):
                analts = datetime.fromtimestamp(analts)

            convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)
            doses = chron.get_doses()
            segments = [(pwr, convert_days(en - st), convert_days(analts - st))
                        for pwr, st, en in doses
                        if st is not None and en is not None]

            d_o = doses[0][1]
            self.irradiation_time = time.mktime(d_o.timetuple()) if d_o else 0
            self.chron_segments = segments
            self.chron_dosages = doses

    def _sync_interference_corrections(self, level):
        pr = level.production

        prs = dict()
        for pk in INTERFERENCE_KEYS:
            v, e = getattr(pr, pk), getattr(pr, '{}_err'.format(pk))
            if v is None:
                v = 0
            if e is None:
                e = 0

            prs[pk.lower()] = ufloat(v, e, tag=pk)

        self.interference_corrections = prs

        # def _sync_view(self, av=None):
        #     if av is None:
        #         av = self.analysis_view
        #     try:
        #         av.load(self)
        #     except BaseException, e:
        #         print 'sync view {}'.format(e)

        # av.load(weakref.ref(self)())

    def _sync_detector_info(self, meas_analysis, **kw):
        #discrimination saved as 1amu disc not 4amu
        discriminations = self._get_discriminations(meas_analysis)

        # self.ic_factors = self._get_ic_factors(meas_analysis)
        ics = self._get_ic_factors(meas_analysis)
        for iso in self.isotopes.itervalues():
            det = iso.detector
            try:
                r = ics[det]
            except KeyError:
                r = ufloat(1, 0)

            iso.ic_factor = r
            # iso.ic_factor = self.get_ic_factor(det)

            idisc = ufloat(1, 1e-20)
            if iso.detector in discriminations:
                disc, refmass = discriminations[det]

                mass = iso.mass
                n = mass - refmass

                #calculate discrimination
                idisc = disc ** n
                e = disc
                idisc = ufloat(idisc.nominal_value, e.std_dev, tag='{} D'.format(iso.name))

            iso.discrimination = idisc

    def _sync_isotopes(self, meas_analysis, isos,
                       unpack, load_peak_center=False, selected_histories=None):
        # self.isotopes = timethis(self._get_isotopes, args=(meas_analysis, isos),
        #                          kwargs=dict(unpack=unpack))

        self._make_isotopes(meas_analysis, isos, unpack, selected_histories)

        if load_peak_center:
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
                    icfs[ic.detector.name] = ufloat(ic.user_value,
                                                    ic.user_error,
                                                    tag='{} IC'.format(ic.detector.name))

        return icfs

    def get_isotope_fits(self):
        keys = self.isotope_keys
        isos = self.isotopes
        fs, bs = [], []
        for k in keys:
            iso = isos[k]
            fs.append((iso.fit, iso.error_type, iso.filter_outliers_dict))
            iso = iso.baseline
            bs.append((iso.fit, iso.error_type, iso.filter_outliers_dict))

        return fs + bs

    def _make_isotopes(self, meas_analysis, dbisos, unpack, selected_histories):
        # isotopes = dict()
        self.isotopes = dict()
        # timethis(self._get_signals, args=(isotopes, meas_analysis, dbisos, unpack))
        # timethis(self._get_baselines, args=(isotopes, meas_analysis, dbisos, unpack))
        # timethis(self._get_blanks, args=(isotopes, meas_analysis))
        self._get_signals(meas_analysis, dbisos, unpack, selected_histories)
        self._get_baselines(meas_analysis, dbisos, unpack, selected_histories)

        self._get_blanks(meas_analysis, selected_histories)

    def _get_signals(self, meas_analysis, dbisos, unpack, selected_histories):
        d = self.isotopes
        default_fit = self._default_fit_factory('linear', 'SEM')
        for iso in dbisos:
            mw = iso.molecular_weight
            # print iso.kind, iso.detector
            if not iso.kind == 'signal' or not mw:
                continue
            if not iso.detector:
                continue

            det = iso.detector.name
            isoname = mw.name
            key = isoname
            if isoname in d:
                key = '{}{}'.format(isoname, det)

            result = None
            # todo: this needs to be fixed to handle data_reduction_tag
            # if analysis has a dr tag then get its associated select_histories entry
            # the get the select_fits then the associated results
            if selected_histories is None:
                try:
                    result = iso.results[-1]
                except IndexError:
                    result = None
            r = Isotope(mass=mw.mass,
                        dbrecord=iso,
                        dbresult=result,
                        name=isoname,
                        detector=det,
                        unpack=unpack)
            if r.unpack_error:
                self.warning('Bad isotope {} {}. error: {}'.format(self.record_id, key, r.unpack_error))
                self.temp_status = 1
            else:
                fit = self.get_db_fit(meas_analysis, isoname, 'signal', selected_histories)
                if fit is None:
                    fit = default_fit()
                r.set_fit(fit, notify=False)
                d[key] = r

    def _get_baselines(self, meas_analysis, dbisos, unpack, selected_histories):
        isotopes = self.isotopes
        default_fit = self._default_fit_factory('average', 'SEM')
        for dbiso in dbisos:
            mw = dbiso.molecular_weight
            if not mw:
                continue

            name = mw.name
            det = dbiso.detector.name
            try:
                iso = isotopes['{}{}'.format(name, det)]
            except KeyError:
                iso = isotopes[name]

            kw = dict(dbrecord=dbiso,
                      name=name,
                      detector=det,
                      unpack=unpack)

            kind = dbiso.kind
            if kind == 'baseline':
                result = None
                if selected_histories is None:
                    # todo: this needs to be fixed to handle data_reduction_tag
                    try:
                        result = dbiso.results[-1]
                    except IndexError:
                        result = None

                kw['name'] = '{} bs'.format(name)
                r = Baseline(dbresult=result, **kw)
                fit = self.get_db_fit(meas_analysis, name, 'baseline', selected_histories)
                if fit is None:
                    fit = default_fit()

                r.set_fit(fit, notify=False)
                iso.baseline = r
            elif kind == 'sniff' and unpack:
                r = Sniff(**kw)
                iso.sniff = r

    def _default_fit_factory(self, fit, error):
        def factory():
            return Fit(fit=fit,
                       error_type=error,
                       filter_outliers=False,
                       filter_outlier_iterations=1,
                       filter_outlier_std_devs=2,
                       include_baseline_error=False,
                       time_zero_offset=0)

        return factory

    def sync_blanks(self, meas_analysis):
        self.debug('syncing blanks age={}'.format(self.uage))
        av = self.analysis_view
        hv = av.history_view
        mv = av.main_view

        bid = meas_analysis.selected_histories.selected_blanks_id
        self.selected_blanks_id = bid

        for bi in self.blank_changes:
            bi.active = bi.id == bid

        if hv:
            hv.selected_blanks_id = bid

            hv.blank_changes = self.blank_changes
            hv.refresh_needed = True

        self._get_blanks(meas_analysis)
        self.calculate_age(force=True)
        self.debug('post sync blanks age={}'.format(self.uage))
        if mv:
            mv.load_computed(self, new_list=False)
            mv.refresh_needed = True

    # def _get_blanks(self, selected_histories):
    def _get_blanks(self, meas_analysis, selected_histories=None):
        isotopes = self.isotopes

        if selected_histories is None:
            selected_histories = meas_analysis.selected_histories

        if selected_histories:
            history = selected_histories.selected_blanks
            keys = isotopes.keys()
            if history:
                for ba in history.blanks:
                    isok = ba.isotope
                    try:
                        blank = isotopes[isok].blank
                        blank.name = n = '{} bk'.format(isok)
                        # if isok=='Ar40':
                        #     print ba.user_value
                        blank.set_uvalue((ba.user_value,
                                          ba.user_error), dirty=False)
                        blank.uvalue.tag = n
                        blank.trait_setq(fit=ba.fit or '')
                        keys.remove(isok)
                        if not keys:
                            break
                    except KeyError:
                        pass

            # set names for isotopes with no blank
            for k in keys:
                blank = isotopes[k].blank
                n = '{} bk'.format(k)
                blank.uvalue.tag = n
                blank.name = n

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

    # def _get_analysis_type(self, meas_analysis):
    #     r = ''
    #     if meas_analysis:
    #         r = meas_analysis.measurement.analysis_type.name
    #     return r

    # def _get_mass_spectrometer(self, meas_analysis):
    #     return meas_analysis.measurement.mass_spectrometer.name.lower()

    def _get_discriminations(self, meas_analysis):
        """
            discriminations should be saved as 1amu not 4amu
        """
        d = dict()
        if meas_analysis.selected_histories:
            selected_hist = meas_analysis.selected_histories.selected_detector_param
            if selected_hist:
                for dp in selected_hist.detector_params:
                    self.discrimination = disc = ufloat(dp.disc, dp.disc_error)
                    d[dp.detector.name] = (disc, dp.refmass)
                    # d[dp.detector.name] = (ufloat(1.004, 0.000145), dp.refmass)
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

# ============= EOF =============================================
