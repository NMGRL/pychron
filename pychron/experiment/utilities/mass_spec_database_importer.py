#===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Instance, Button
from traitsui.api import View, Item

#============= standard library imports ========================
import struct
from numpy import array
#============= local library imports  ==========================
from pychron.helpers.isotope_utils import sort_isotopes
from pychron.loggable import Loggable
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.regression.ols_regressor import PolynomialRegressor
from pychron.regression.mean_regressor import MeanRegressor
from uncertainties import ufloat
from pychron.experiment.utilities.info_blob import encode_infoblob
import time

mkeys = ['l2 value', 'l1 value', 'ax value', 'h1 value', 'h2 value']

'''
following information is necessary


'''

RUN_TYPE_DICT = dict(Unknown=1, Air=2, Blank=5)
# SAMPLE_DICT = dict(Air=2, Blank=1)
ISO_LABELS = dict(H1='Ar40', AX='Ar39', L1='Ar38', L2='Ar37', CDD='Ar36')

DEBUG = True


class MassSpecDatabaseImporter(Loggable):
    db = Instance(MassSpecDatabaseAdapter)
    test = Button
    sample_loading_id = None
    data_reduction_session_id = None
    login_session_id = None
    _current_spec = None
    _analysis = None

    def connect(self):
        return self.db.connect()

    def add_sample_loading(self, ms, tray):
        if self.sample_loading_id is None:
            db = self.db
            with db.session_ctx() as sess:
                sl = db.add_sample_loading(ms, tray)
                sess.flush()
                #             db.flush()
                self.sample_loading_id = sl.SampleLoadingID

    def add_login_session(self, ms):
        self.info('adding new session for {}'.format(ms))
        db = self.db
        with db.session_ctx() as sess:
            ls = db.add_login_session(ms)
            sess.flush()
            #         db.flush()
            self.login_session_id = ls.LoginSessionID

    def add_data_reduction_session(self):
        if self.data_reduction_session_id is None:
            db = self.db
            with db.session_ctx() as sess:
                dr = db.add_data_reduction_session()
                sess.flush()
                #             db.flush()
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

    def add_analysis(self, spec, commit=True):
        with self.db.session_ctx(commit=False) as sess:
            irradpos = spec.irradpos
            rid = spec.rid
            trid = rid.lower()

            if trid.startswith('b'):
                runtype = 'Blank'
                irradpos = -1
            elif trid.startswith('a'):
                runtype = 'Air'
                irradpos = -2
            elif trid.startswith('c'):
                runtype = 'Unknown'
                if spec.spectrometer.lower() in ('obama', 'pychron obama'):
                    rid = '4358'
                    irradpos = '4358'
                else:
                    rid = '4359'
                    irradpos = '4359'

                paliquot = self.db.get_lastest_analysis_aliquot(rid)
                self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%% paliqout{} {}'.format(paliquot, rid))
                if paliquot is None:
                    paliquot = 0

                aliquot = paliquot + 1
                rid = '{}-{:02n}'.format(rid, aliquot)
                spec.aliquot = '{:02n}'.format(aliquot)
            else:
                runtype = 'Unknown'

            self._analysis = None
            try:
                return self._add_analysis(sess, spec, irradpos, rid, runtype)
            except Exception, e:
                import traceback

                tb = traceback.format_exc()
                self.message('Could not save to Mass Spec database.\n {}'.format(tb))
                if commit:
                    sess.rollback()
                    #                 self.db.rollback()
                    #                 pid = spec.rid
                    #                 spec.aliquot = '*{:02n}'.format(spec.aliquot)
                    #                 spec.rid = '{}-{}'.format(spec.labnumber, spec.aliquot)
                    #                 self.message('Saving {} as {}'.format(pid, spec.rid))
                    #                 self._add_analysis(spec, irradpos, spec.rid, runtype, commit)


                    #    def _add_analysis(self, *args):
                    #        db=self.db
                    #        with db.session_ctx() as sess:
                    #            self._add_analysis_db(sess,*args)

    def _add_analysis(self, sess, spec, irradpos, rid, runtype):

        gst = time.time()

        db = self.db

        spectrometer = spec.spectrometer
        tray = spec.tray

        pipetted_isotopes = self._make_pipetted_isotopes(runtype)

        #=======================================================================
        # add analysis
        #=======================================================================
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
                    'no irradiation position found for {}. not importing analysis {}'.format(irradpos, spec.record_id))
                return
                # add runscript
        rs = db.add_runscript(spec.runscript_name,
                              spec.runscript_text)

        self.create_import_session(spectrometer, tray)

        # add the reference detector
        refdbdet = db.add_detector('H1', Label='H1')

        # remember new rid in case duplicate entry error and need to augment rid
        spec.rid = rid
        analysis = db.add_analysis(rid, spec.aliquot, spec.step,
                                   irradpos,
                                   RUN_TYPE_DICT[runtype],
                                   #                                   'H1',
                                   RedundantSampleID=sample_id,
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
                                   ReferenceDetectorLabel=refdbdet.Label,
                                   SampleLoadingID=self.sample_loading_id,
                                   LoginSessionID=self.login_session_id,
                                   RunScriptID=rs.RunScriptID)

        db.add_analysis_positions(analysis, spec.position)
        #=======================================================================
        # add changeable items
        #=======================================================================
        item = db.add_changeable_items(analysis, self.data_reduction_session_id)

        self.debug('%%%%%%%%%%%%%%%%%%%% Comment: {} %%%%%%%%%%%%%%%%%%%'.format(spec.comment))
        item.Comment = spec.comment
        #sess.flush()
        analysis.ChangeableItemsID = item.ChangeableItemsID

        self._add_isotopes(analysis, spec, refdbdet, runtype)
        sess.flush()

        t = time.time() - gst
        self.debug('{} added analysis time {}s'.format(spec.record_id, t))
        return analysis

    def _add_isotopes(self, analysis, spec, refdet, runtype):
        with spec.open_file():
            isotopes = list(spec.iter_isotopes())
            isotopes = sort_isotopes(isotopes, key=lambda x: x[0])

            bs = []
            for iso, det in isotopes:
                self.debug('adding isotope {} {}'.format(iso, det))
                dbiso, dbdet = self._add_isotope(analysis, spec, iso, det, refdet)

                if not dbdet.Label in bs:
                    self._add_baseline(spec, dbiso, dbdet, det)
                    bs.append(dbdet.Label)

                self._add_signal(spec, dbiso, dbdet, det, runtype)

    def _add_isotope(self, analysis, spec, iso, det, refdet):
        db = self.db
        if det == analysis.ReferenceDetectorLabel:
            dbdet = refdet
        else:

            """
                if is_peak_hop
                fool mass spec. e.g Ar40 det = H1 not CDD
                det=PEAK_HOP_MAP['Ar40']=='CDD'
            """
            PEAK_HOP_MAP = {'Ar41': 'H2', 'Ar40': 'H1',
                            'Ar39': 'AX', 'Ar38': 'L1',
                            'Ar37': 'L2', 'Ar36': 'CDD'}

            if spec.is_peak_hop:
                det = PEAK_HOP_MAP[iso]

            dbdet = db.add_detector(det, Label=det)
            if det == 'CDD':
                dbdet.ICFactor = spec.ic_factor_v
                dbdet.ICFactorEr = spec.ic_factor_e

        return db.add_isotope(analysis, dbdet, iso), dbdet

    def _add_signal(self, spec, dbiso, dbdet, odet, runtype):
        #===================================================================
        # peak time
        #===================================================================
        """
            build two blobs
            blob 1 PeakTimeBlob
            x, y - mean(baselines)

            blob 2
            y list
        """
        db = self.db

        iso = dbiso.Label
        det = dbdet.Label

        tb, vb = spec.get_signal_data(iso, odet)

        baseline = spec.get_baseline_uvalue(det)
        vb = array(vb) - baseline.nominal_value
        blob1 = self._build_timeblob(tb, vb)

        blob2 = [struct.pack('>f', float(v)) for v in vb]
        db.add_peaktimeblob(blob1, blob2, dbiso)

        # in mass spec the intercept is already baseline corrected
        # mass spec also doesnt propagate baseline errors

        signal = spec.get_signal_uvalue(iso, det)
        sfit = spec.get_signal_fit(iso, det)

        if runtype == 'Blank':
            ublank = signal - baseline
        else:
            ublank = spec.get_blank_uvalue(iso)

        db.add_isotope_result(dbiso, self.data_reduction_session_id,
                              signal,
                              baseline,
                              ublank,
                              sfit,
                              dbdet)

    def _add_baseline(self, spec, dbiso, dbdet, odet):
        self.debug('add baseline dbdet= {}. original det= {}'.format(dbdet.Label, odet))

        det = dbdet.Label
        tb, vb = spec.get_baseline_data(dbiso.Label, odet)
        blob = self._build_timeblob(tb, vb)

        db = self.db
        label = '{} Baseline'.format(det.upper())
        ncnts = len(tb)
        db_baseline = db.add_baseline(blob, label, ncnts, dbiso)

        if spec.is_peak_hop:
            det = spec.peak_hop_detector

        bs = spec.get_baseline_uvalue(det)

        sem = bs.std_dev / (ncnts) ** 0.5

        bfit = spec.get_baseline_fit(det)

        infoblob = self._make_infoblob(bs.nominal_value, sem)
        db_changeable = db.add_baseline_changeable_item(self.data_reduction_session_id,
                                                        bfit,
                                                        infoblob)

        # baseline and baseline changeable items need matching BslnID
        db_changeable.BslnID = db_baseline.BslnID

    def _make_pipetted_isotopes(self, runtype):
        blob = ''
        if runtype == 'Air':
            isos = []
            for a, v in (('Ar40', 295.5e-13), ('Ar38', 0.19e-13), ('Ar36', 1e-13)):
                isos.append('{}\t{}'.format(a, v))
            blob = '\r'.join(isos)
        return blob

    def _build_timeblob(self, t, v):
        """
        """
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', float(vi), float(ti))
        return blob

    def _make_infoblob(self, baseline, baseline_err):
        rpts = 0
        pos_segments = []
        bs_segments = [1.0000000200408773e+20]
        bs_seg_params = [[baseline, 0, 0, 0]]
        bs_seg_errs = [baseline_err]
        b = encode_infoblob(rpts, pos_segments, bs_segments, bs_seg_params, bs_seg_errs)
        return b


    #===========================================================================
    # debugging
    #===========================================================================
    def _test_fired(self):
        import numpy as np

        self.db.connect()
        xbase = np.linspace(430, 580, 150)
        #        ybase = np.zeros(150)
        #        cddybase = np.zeros(150)
        ybase = np.random.random(150)
        cddybase = np.random.random(150) * 0.001

        base = [zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, cddybase),
        ]

        xsig = np.linspace(20, 420, 410)
        #        y40 = np.ones(410) * 680
        #        y39 = np.ones(410) * 107
        #        y38 = np.zeros(410) * 1.36
        #        y37 = np.zeros(410) * 0.5
        #        y36 = np.ones(410) * 0.001

        y40 = 680 - 0.1 * xsig
        y39 = 107 - 0.1 * xsig
        y38 = np.zeros(410) * 1.36
        y37 = np.zeros(410) * 0.5
        y36 = 1 + 0.1 * xsig

        sig = [zip(xsig, y40),
               zip(xsig, y39),
               zip(xsig, y38),
               zip(xsig, y37),
               zip(xsig, y36),

        ]

        regbs = MeanRegressor(xs=xbase, ys=ybase)
        cddregbs = MeanRegressor(xs=xbase, ys=cddybase)
        reg = PolynomialRegressor(xs=xsig, ys=y40, fit='linear')

        reg1 = PolynomialRegressor(xs=xsig, ys=y39, fit='linear')
        reg2 = PolynomialRegressor(xs=xsig, ys=y38, fit='linear')
        reg3 = PolynomialRegressor(xs=xsig, ys=y37, fit='linear')
        reg4 = PolynomialRegressor(xs=xsig, ys=y36, fit='linear')

        keys = [
            ('H1', 'Ar40'),
            ('AX', 'Ar39'),
            ('L1', 'Ar38'),
            ('L2', 'Ar37'),
            ('CDD', 'Ar36'),
        ]

        regresults = (dict(
            Ar40=ufloat(reg.predict(0), reg.predict_error(0)),
            Ar39=ufloat(reg1.predict(0), reg1.predict_error(0)),
            Ar38=ufloat(reg2.predict(0), reg2.predict_error(0)),
            Ar37=ufloat(reg3.predict(0), reg3.predict_error(0)),
            Ar36=ufloat(reg4.predict(0), reg4.predict_error(0)),

        ),
                      dict(
                          Ar40=ufloat(regbs.predict(0), regbs.predict_error(0)),
                          Ar39=ufloat(regbs.predict(0), regbs.predict_error(0)),
                          Ar38=ufloat(regbs.predict(0), regbs.predict_error(0)),
                          Ar37=ufloat(regbs.predict(0), regbs.predict_error(0)),
                          Ar36=ufloat(cddregbs.predict(0), cddregbs.predict_error(0))
                      ))
        blanks = [ufloat(0, 0.1),
                  ufloat(0.1, 0.001),
                  ufloat(0.01, 0.001),
                  ufloat(0.01, 0.001),
                  ufloat(0.00001, 0.0001),
        ]
        fits = (
            dict(zip(['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'],
                     ['Linear', 'Linear', 'Linear', 'Linear', 'Linear'])),
            dict(zip(['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'],
                     ['Average Y', 'Average Y', 'Average Y', 'Average Y', 'Average Y'])))
        mass_spectrometer = 'obama'
        extract_device = 'Laser Furnace'
        extract_value = 10
        position = 1
        duration = 10
        first_stage_delay = 0
        second_stage_delay = 30
        tray = '100-hole'
        runscript_name = 'Foo'
        runscript_text = 'this is a test script'

        self.add_analysis('4318', '500', '', '4318',
                          base, sig, blanks,
                          keys,
                          regresults,
                          fits,

                          mass_spectrometer,
                          extract_device,
                          tray,
                          position,
                          extract_value, # power requested
                          extract_value, # power achieved

                          duration, # total extraction
                          duration, # time at extract_value

                          first_stage_delay,
                          second_stage_delay,

                          runscript_name,
                          runscript_text,
        )

    def traits_view(self):
        v = View(Item('test', show_label=False))
        return v

    def _db_default(self):
        db = MassSpecDatabaseAdapter(kind='mysql',
                                     host='localhost',
                                     username='root',
                                     password='Argon',
                                     name='massspecdata_import'
                                     #                                     host='129.138.12.131',
                                     #                                     username='massspec',
                                     #                                     password='DBArgon',
                                     #                                     name='massspecdata_isotopedb'
        )
        #        db.connect()

        return db


if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    logging_setup('db_import')
    d = MassSpecDatabaseImporter()

    d.configure_traits()

    #============= EOF ====================================
    #        from pychron.codetools.simple_timeit import timethis
    #        for ((det, isok), si, bi, ublank, signal, baseline, sfit, bfit) in spec.iter():
    #            self.debug('msi {} {} {} {} {} {}'.format(det, isok, signal.nominal_value,
    #                                                      baseline.nominal_value, sfit, bfit))
    #            #===================================================================
    #            # isotopes
    #            #===================================================================
    #
    ##            db_iso = timethis(db.add_isotope, args=(analysis, det, isok),
    ##                              msg='add_isotope', log=self.debug, decorate='^')
    #
    #            # add detector
    #            if det == analysis.ReferenceDetectorLabel:
    #                dbdet = refdbdet
    #            else:
    #                dbdet = db.add_detector(det, Label=det)
    #                if det == 'CDD':
    #                    dbdet.ICFactor = spec.ic_factor_v
    #                    dbdet.ICFactorEr = spec.ic_factor_e
    #                    sess.flush()
    #
    #            db_iso = db.add_isotope(analysis, dbdet, isok)
    #            #===================================================================
    #            # baselines
    #            #===================================================================
    #            self.debug(bi)
    #            tb, vb = zip(*bi)
    #            blob = self._build_timeblob(tb, vb)
    #            label = '{} Baseline'.format(det.upper())
    #            ncnts = len(tb)
    #            db_baseline = db.add_baseline(blob, label, ncnts, db_iso)
    #
    #            sem = baseline.std_dev / (ncnts) ** 0.5
    #            infoblob = self._make_infoblob(baseline.nominal_value, sem)
    #            db_changeable = db.add_baseline_changeable_item(self.data_reduction_session_id,
    #                                                            bfit,
    #                                                            infoblob,
    #                                                            )
    #
    #            # baseline and baseline changeable items need matching BslnID
    #            db_changeable.BslnID = db_baseline.BslnID
    #            #===================================================================
    #            # peak time
    #            #===================================================================
    #            '''
    #                build two blobs
    #                blob 1 PeakTimeBlob
    #                x, y - mean(baselines)
    #
    #                blob 2
    #                y list
    #            '''
    #            tb, vb = zip(*si)
    #            vb = array(vb) - baseline.nominal_value
    #            blob1 = self._build_timeblob(tb, vb)
    #
    #            blob2 = [struct.pack('>f', float(v)) for v in vb]
    #            db.add_peaktimeblob(blob1, blob2, db_iso)
    #
    #            # in mass spec the intercept is alreay baseline corrected
    #            # mass spec also doesnt propograte baseline errors
    #
    #            if runtype == 'Blank':
    #                ublank = signal - baseline
    #
    #            db.add_isotope_result(db_iso, self.data_reduction_session_id,
    #                                  signal,
    #                                  baseline,
    #                                  ublank,
    #                                  sfit,
    #                                  dbdet,)