# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Instance, Int, Str, Bool, provides
# ============= standard library imports ========================
from datetime import datetime
import struct
from numpy import array
import time
import os
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.i_datastore import IDatastore
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.experiment.utilities.identifier import make_runid
from pychron.experiment.utilities.identifier_mapper import IdentifierMapper
from pychron.loggable import Loggable
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.experiment.utilities.info_blob import encode_infoblob
from pychron.pychron_constants import ALPHAS

mkeys = ['l2 value', 'l1 value', 'ax value', 'h1 value', 'h2 value']

'''
following information is necessary


'''

RUN_TYPE_DICT = dict(Unknown=1, Air=2, Blank=5)
# SAMPLE_DICT = dict(Air=2, Blank=1)
# ISO_LABELS = dict(H1='Ar40', AX='Ar39', L1='Ar38', L2='Ar37', CDD='Ar36')

PEAK_HOP_MAP = {'Ar41': 'H2', 'Ar40': 'H1',
                'Ar39': 'AX', 'Ar38': 'L1',
                'Ar37': 'L2', 'Ar36': 'CDD'}

DBVERSION = float(os.environ.get('MassSpecDBVersion', 16.3))


@provides(IDatastore)
class MassSpecDatabaseImporter(Loggable):
    precedence = Int(0)

    identifier_mapper = Instance(IdentifierMapper, ())
    db = Instance(MassSpecDatabaseAdapter)

    sample_loading_id = None
    data_reduction_session_id = None
    login_session_id = None

    reference_detector_name = Str
    reference_isotope_name = Str
    use_reference_detector_by_isotope = Bool

    _current_spec = None
    _analysis = None
    _database_version = 0

    # IDatastore protocol
    def get_greatest_step(self, identifier, aliquot):

        ret = 0
        if self.db:
            identifier = self.get_identifier(identifier)
            ret = self.db.get_latest_analysis(identifier, aliquot)
            if ret:
                _, s = ret
                if s is not None and s in ALPHAS:
                    ret = ALPHAS.index(s)  # if s is not None else -1
                else:
                    ret = -1
        return ret

    def get_greatest_aliquot(self, identifier):
        ret = 0
        if self.db:
            identifier = self.get_identifier(identifier)
            ret = self.db.get_latest_analysis(identifier)
            if ret:
                ret, _ = ret
        return ret

    def is_connected(self):
        if self.db:
            return self.db.connected

    def connect(self, *args, **kw):
        ret = self.db.connect(*args, **kw)
        if ret:
            ver = self.db.get_database_version()
            if ver is not None:
                self._database_version = ver

        return ret

    def add_sample_loading(self, ms, tray):
        if self.sample_loading_id is None:
            db = self.db
            with db.session_ctx() as sess:
                sl = db.add_sample_loading(ms, tray)
                sess.flush()
                self.sample_loading_id = sl.SampleLoadingID

    def add_login_session(self, ms):
        self.info('adding new session for {}'.format(ms))
        db = self.db
        with db.session_ctx() as sess:
            ls = db.add_login_session(ms)
            sess.flush()
            self.login_session_id = ls.LoginSessionID

    def add_data_reduction_session(self):
        if self.data_reduction_session_id is None:
            db = self.db
            with db.session_ctx() as sess:
                dr = db.add_data_reduction_session()
                sess.flush()
                self.data_reduction_session_id = dr.DataReductionSessionID

    def create_import_session(self, spectrometer, tray):
        # add login, sample, dr ids
        if self.login_session_id is None or self._current_spec != spectrometer:
            self._current_spec = spectrometer
            self.add_login_session(spectrometer)

        if self.data_reduction_session_id is None:
            self.add_data_reduction_session()
        if self.sample_loading_id is None:
            self.add_sample_loading(spectrometer, tray)

    def clear_import_session(self):
        self.sample_loading_id = None
        self.data_reduction_session_id = None
        self.login_session_id = None
        self._current_spec = None

    def get_identifier(self, spec):
        """
            convert cocktails into mass spec labnumbers

            spec is either ExportSpec, int or str
            return identifier
        """

        if isinstance(spec, (int, str)):
            identifier = spec
            mass_spectrometer = ''
            if isinstance(identifier, str):
                if '-' in identifier:
                    a = identifier.split('-')[-1]
                    if a.lower() == 'o':
                        mass_spectrometer = 'obama'
                    elif a.lower() == 'j':
                        mass_spectrometer = 'jan'
                    elif a.lower() == 'f':
                        mass_spectrometer = 'felix'
        else:
            mass_spectrometer = spec.mass_spectrometer.lower()

        identifier = str(spec if isinstance(spec, (int, str)) else spec.labnumber)

        return self.identifier_mapper.map_to_value(identifier, mass_spectrometer, 'MassSpec')

    def add_irradiation(self, irrad, level, pid):
        with self.db.session_ctx():
            sid = 0
            self.db.add_irradiation_level(irrad, level, sid, pid)

    def add_irradiation_position(self, identifier, levelname, hole, **kw):
        with self.db.session_ctx():
            return self.db.add_irradiation_position(identifier, levelname, hole, **kw)

    def add_irradiation_production(self, name, prdict, ifdict):
        with self.db.session_ctx():
            return self.db.add_irradiation_production(name, prdict, ifdict)

    def add_irradiation_chronology(self, irrad, doses):

        with self.db.session_ctx():
            for pwr, st, et in doses:
                self.db.add_irradiation_chronology_segment(irrad, st, et)

    def add_analysis(self, spec, commit=True):
        for i in range(3):
            with self.db.session_ctx(commit=False) as sess:
                irradpos = spec.irradpos
                rid = spec.runid
                trid = rid.lower()
                identifier = spec.labnumber

                if trid.startswith('b'):
                    runtype = 'Blank'
                    irradpos = -1
                elif trid.startswith('a'):
                    runtype = 'Air'
                    irradpos = -2
                elif trid.startswith('c'):
                    runtype = 'Unknown'
                    identifier = irradpos = self.get_identifier(spec)
                else:
                    runtype = 'Unknown'

                rid = make_runid(identifier, spec.aliquot, spec.step)

                self._analysis = None
                self.db.reraise = True
                try:
                    ret = self._add_analysis(sess, spec, irradpos, rid, runtype)
                    sess.commit()
                    return ret
                except Exception, e:
                    import traceback
                    tb = traceback.format_exc()
                    self.debug('Mass Spec save exception. {}\n {}'.format(e, tb))
                    if i == 2:
                        self.message('Could not save spec.runid={} rid={} '
                                     'to Mass Spec database.\n {}'.format(spec.runid, rid, tb))
                    else:
                        self.debug('retry mass spec save')
                    # if commit:
                    sess.rollback()
                finally:
                    self.db.reraise = True

    def _add_analysis(self, sess, spec, irradpos, rid, runtype):

        gst = time.time()

        db = self.db

        spectrometer = spec.mass_spectrometer
        if spectrometer.lower() == 'argus':
            spectrometer = 'UM'

        tray = spec.tray

        pipetted_isotopes = self._make_pipetted_isotopes(runtype)

        # =======================================================================
        # add analysis
        # =======================================================================
        # get the sample_id
        sample_id = 0
        if runtype == 'Air':
            sample = db.get_sample('Air')
            if sample:
                sample_id = sample.SampleID
        else:
            db_irradpos = db.get_irradiation_position(irradpos)
            if db_irradpos:
                sample_id = db_irradpos.SampleID
            else:
                self.warning(
                    'no irradiation position found for {}. not importing analysis {}'.format(irradpos, spec.runid))
                return
                # add runscript
        rs = db.add_runscript(spec.runscript_name,
                              spec.runscript_text)

        self.create_import_session(spectrometer, tray)

        if not self.reference_isotope_name:
            self.reference_isotope_name = 'Ar40'

        if self.use_reference_detector_by_isotope:
            rd = spec.get_detector_by_isotope(self.reference_isotope_name)
        else:
            if not self.reference_detector_name:
                self.reference_detector_name = 'H1'
            rd = self.reference_detector_name

        self.debug('Reference Isotope={}'.format(self.reference_isotope_name))
        self.debug('Reference Detector={}'.format(rd))

        # add the reference detector
        if DBVERSION >= 16.3:
            refdbdet = db.add_detector(rd)
        else:
            refdbdet = db.add_detector(rd, Label=rd)

        sess.flush()

        spec.runid = rid

        params = dict(RedundantSampleID=sample_id,
                      HeatingItemName=spec.extract_device,
                      PwrAchieved=spec.power_achieved,
                      PwrAchieved_Max=spec.power_achieved,
                      PwrAchievedSD=0,
                      FinalSetPwr=spec.power_requested,
                      TotDurHeating=spec.duration,
                      TotDurHeatingAtReqPwr=spec.duration_at_request,
                      FirstStageDly=spec.first_stage_delay,
                      SecondStageDly=spec.second_stage_delay,
                      PipettedIsotopes=pipetted_isotopes,
                      RefDetID=refdbdet.DetectorID,
                      SampleLoadingID=self.sample_loading_id,
                      LoginSessionID=self.login_session_id,
                      RunScriptID=rs.RunScriptID)
        if DBVERSION >= 16.3:
            params['SignalRefIsot'] = self.reference_isotope_name
            params['RedundantUserID'] = 1

        else:
            params['ReferenceDetectorLabel'] = refdbdet.Label

        analysis = db.add_analysis(rid, spec.aliquot, spec.step,
                                   irradpos,
                                   RUN_TYPE_DICT[runtype], **params)
        sess.flush()
        if spec.update_rundatetime:
            d = datetime.fromtimestamp(spec.timestamp)
            analysis.RunDateTime = d
            analysis.LastSaved = d

        db.add_analysis_positions(analysis, spec.position)
        # =======================================================================
        # add changeable items
        # =======================================================================
        item = db.add_changeable_items(analysis, self.data_reduction_session_id)

        self.debug('%%%%%%%%%%%%%%%%%%%% Comment: {} %%%%%%%%%%%%%%%%%%%'.format(spec.comment))
        item.Comment = spec.comment
        sess.flush()
        analysis.ChangeableItemsID = item.ChangeableItemsID

        self._add_isotopes(analysis, spec, refdbdet, runtype)
        sess.flush()

        t = time.time() - gst
        self.debug('{} added analysis time {}s'.format(spec.runid, t))
        return analysis

    def _add_isotopes(self, analysis, spec, refdet, runtype):
        # with spec.open_file():
        isotopes = list(spec.iter_isotopes())
        isotopes = sort_isotopes(isotopes, key=lambda x: x[0])

        bs = []
        for iso, det in isotopes:
            self.debug('adding isotope {} {}'.format(iso, det))
            dbiso, dbdet = self._add_isotope(analysis, spec, iso, det, refdet)

            if dbdet.detector_type.Label not in bs:
                self._add_baseline(spec, dbiso, dbdet, det)
                bs.append(dbdet.detector_type.Label)

            self._add_signal(spec, dbiso, dbdet, det, runtype)

    def _add_isotope(self, analysis, spec, iso, det, refdet):
        db = self.db

        if DBVERSION >= 16.3:
            rdet = analysis.reference_detector.detector_type.Label
        else:
            rdet = analysis.ReferenceDetectorLabel

        if det == rdet:
            dbdet = refdet
        else:
            if spec.is_peak_hop:
                """
                if is_peak_hop
                fool mass spec. e.g Ar40 det = H1 not CDD
                det=PEAK_HOP_MAP['Ar40']=='CDD'
                """

                if iso in PEAK_HOP_MAP:
                    det = PEAK_HOP_MAP[iso]

            if DBVERSION >= 16.3:
                dbdet = db.add_detector(det)
            else:
                dbdet = db.add_detector(det, Label=det)

            ic = spec.isotopes[iso].ic_factor
            dbdet.ICFactor = float(nominal_value(ic))
            dbdet.ICFactorEr = float(std_dev(ic))

        db.flush()
        n = spec.get_ncounts(iso)
        return db.add_isotope(analysis, dbdet, iso, NumCnts=n), dbdet

    def _add_signal(self, spec, dbiso, dbdet, odet, runtype):
        # ===================================================================
        # peak time
        # ===================================================================
        """
            build two blobs
            blob 1 PeakTimeBlob
            x, y -

            blob 2
            y list
        """
        db = self.db

        iso = dbiso.Label
        det = dbdet.detector_type.Label

        tb, vb = spec.get_signal_data(iso, odet)

        # baseline = spec.get_baseline_uvalue(iso)
        baseline, fncnts = spec.get_filtered_baseline_uvalue(iso)

        cvb = array(vb) - baseline.nominal_value
        blob1 = self._build_timeblob(tb, cvb)

        blob2 = ''.join([struct.pack('>f', v) for v in vb])
        db.add_peaktimeblob(blob1, blob2, dbiso)

        # @todo: add filtered points blob

        # in mass spec the intercept is already baseline corrected
        # mass spec also doesnt propagate baseline errors

        signal = spec.get_signal_uvalue(iso, det)
        sfit = spec.get_signal_fit(iso)

        is_blank = runtype == 'Blank'
        if is_blank:
            ublank = signal - nominal_value(baseline)
        else:
            ublank = spec.get_blank_uvalue(iso)

        db.add_isotope_result(dbiso, self.data_reduction_session_id,
                              signal,
                              baseline,
                              ublank,
                              sfit,
                              dbdet,
                              is_blank=is_blank)

    def _add_baseline(self, spec, dbiso, dbdet, odet):
        iso = dbiso.Label
        self.debug('add baseline dbdet= {}. original det= {}'.format(iso, odet))
        det = dbdet.detector_type.Label
        tb, vb = spec.get_baseline_data(iso, odet)
        pos = spec.get_baseline_position(iso)
        blob = self._build_timeblob(tb, vb)

        db = self.db
        label = '{} Baseline'.format(det.upper())
        ncnts = len(tb)
        db_baseline = db.add_baseline(blob, label, ncnts, dbiso)
        db.flush()
        # if spec.is_peak_hop:
        #     det = spec.peak_hop_detector

        # bs = spec.get_baseline_uvalue(iso)
        bs, fncnts = spec.get_filtered_baseline_uvalue(iso)

        # sem = bs.std_dev / (fncnts) ** 0.5 if fncnts else 0

        bfit = spec.get_baseline_fit(iso)
        self.debug('baseline {}. v={}, e={}'.format(iso, nominal_value(bs), std_dev(bs)))
        infoblob = self._make_infoblob(nominal_value(bs), std_dev(bs), fncnts, pos)
        db_changeable = db.add_baseline_changeable_item(self.data_reduction_session_id,
                                                        bfit,
                                                        infoblob)

        # baseline and baseline changeable items need matching BslnID
        db_changeable.BslnID = db_baseline.BslnID
        db.flush()

    def _make_pipetted_isotopes(self, runtype):
        blob = ''
        if runtype == 'Air':
            isos = []
            for a, v in (('Ar40', 295.5e-13), ('Ar38', 0.18762e-13), ('Ar36', 1e-13)):
                isos.append('{}\t{}'.format(a, v))
            blob = '\r'.join(isos)
        return blob

    def _build_timeblob(self, t, v):
        """
        """
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', vi, ti)
        return blob

    def _make_infoblob(self, baseline, baseline_err, n, baseline_position):
        rpts = n
        pos_segments = [baseline_position]

        bs_segments = [1.0000000200408773e+20]
        bs_seg_params = [[baseline, 0, 0, 0]]
        bs_seg_errs = [baseline_err]
        b = encode_infoblob(rpts, pos_segments, bs_segments, bs_seg_params, bs_seg_errs)
        return b

    def _db_default(self):
        db = MassSpecDatabaseAdapter(kind='mysql', autoflush=False)

        return db

# ============= EOF ====================================
