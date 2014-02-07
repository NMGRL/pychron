#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Instance, Bool, Int, Float, Str, \
    Dict, List, Time, Date, Any, Property
#============= standard library imports ========================
import os
import struct
import time
import math
#============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.codetools.file_log import file_log
from pychron.core.codetools.memory_usage import mem_log
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.ui.preference_binding import bind_preference
from pychron.database.adapters.local_lab_adapter import LocalLabAdapter
from pychron.experiment.automated_run.peak_hop_collector import parse_hops
from pychron.experiment.datahub import Datahub

from pychron.loggable import Loggable
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.paths import paths
from pychron.processing.export.export_spec import ExportSpec
from pychron.pychron_constants import NULL_STR

DEBUG = False


class AutomatedRunPersister(Loggable):
    # db = Instance(IsotopeAdapter)
    local_lab_db = Instance(LocalLabAdapter)
    # massspec_importer = Instance(MassSpecDatabaseImporter)
    datahub = Instance(Datahub)
    run_spec = Instance('pychron.experiment.automated_run.spec.AutomatedRunSpec')
    data_manager = Instance(H5DataManager, ())
    monitor = Any

    default_outlier_filtering = Property(depends_on='filter_outliers, fo_+')
    filter_outliers = Bool(False)
    fo_iterations = Int(1)
    fo_std_dev = Int(2)

    save_as_peak_hop = Bool(False)
    save_enabled = Bool(False)
    experiment_identifier = Int
    sensitivity_multiplier = Float
    experiment_queue_name = Str
    experiment_queue_blob = Str

    extraction_name = Str
    extraction_blob = Str
    measurement_name = Str
    measurement_blob = Str
    positions = List

    #for saving to mass spec
    runscript_name = Str
    runscript_blob = Str

    spec_dict = Dict
    defl_dict = Dict
    active_detectors = List

    previous_blanks = Dict
    secondary_database_fail = False
    use_secondary_database = True

    runid = Str
    uuid = Str
    rundate = Date
    runtime = Time
    load_name = Str

    cdd_ic_factor = Any

    _db_extraction_id = None

    def __init__(self, *args, **kw):
        super(AutomatedRunPersister, self).__init__(*args, **kw)
        self.bind_preferences()

    def bind_preferences(self):
        prefid = 'pychron.experiment'
        bind_preference(self, 'filter_outliers', '{}.filter_outliers'.format(prefid))
        bind_preference(self, 'fo_iterations', '{}.fo_iterations'.format(prefid))
        bind_preference(self, 'fo_std_dev', '{}.fo_std_dev'.format(prefid))

    def get_last_aliquot(self, identifier):
        return self.datahub.get_greatest_aliquot(identifier)

    def writer_ctx(self):
        return self.data_manager.open_file(self._current_data_frame)

    def pre_extraction_save(self):
        d = get_datetime()
        self.runtime = d.time()
        self.rundate = d.date()
        self.info('Analysis started at {}'.format(self.runtime))

    def post_extraction_save(self, rblob, oblob):
        if DEBUG:
            self.debug('Not saving extraction to database')
            return

        db = self.datahub.mainstore.db
        if db:
            with db.session_ctx() as sess:
                loadtable = db.get_loadtable(self.load_name)
                if loadtable is None:
                    loadtable = db.add_load(self.load_name)
                    #             db.flush()

                ext = self._save_extraction(db, loadtable=loadtable,
                                            response_blob=rblob,
                                            output_blob=oblob)
                sess.commit()
                self._db_extraction_id = int(ext.id)
        else:
            self.debug('No database instance')

    def pre_measurement_save(self):
        self.info('pre measurement save')

        dm = self.data_manager
        # make a new frame for saving data

        name = self.uuid
        path = os.path.join(paths.isotope_dir, '{}.h5'.format(name))
        #        path = '/Users/ross/Sandbox/aaaa_multicollect_isotope.h5'

        self._current_data_frame = path
        frame = dm.new_frame(path)

        attrs = frame.root._v_attrs
        attrs['USER'] = self.run_spec.username
        attrs['ANALYSIS_TYPE'] = self.run_spec.analysis_type

        dm.close_file()

    def _local_db_save(self):
        ldb = self._local_lab_db_factory()
        with ldb.session_ctx():
            ln = self.run_spec.labnumber
            aliquot = self.run_spec.aliquot
            step = self.run_spec.step
            uuid = self.uuid
            cp = self._current_data_frame

            ldb.add_analysis(labnumber=ln,
                             aliquot=aliquot,
                             uuid=uuid,
                             step=step,
                             collection_path=cp,
            )
            #ldb.commit()
            #ldb.close()
            #del ldb

    def post_measurement_save(self):
        if DEBUG:
            self.debug('Not measurement saving to database')
            return

        self.info('post measurement save')
        #         mem_log('pre post measurement save')
        if not self.save_enabled:
            self.info('Database saving disabled')
            return

        #check for conflicts immediately before saving
        #automatically update if there is an issue
        conflict = self.datahub.is_conflict(self.run_spec)
        if conflict:
            self.debug('post measurement datastore conflict found. Automatically updating the aliquot and step')
            self.datahub.update_spec(self.run_spec)

        cp = self._current_data_frame

        ln = self.run_spec.labnumber
        aliquot = self.run_spec.aliquot

        # save to local sqlite database for backup and reference
        self._local_db_save()

        # save to a database
        db = self.datahub.mainstore.db
        #         if db and db.connect(force=True):
        if not db or not db.connected:
            self.warning('No database instanc. Not saving post measurement to primary database')
        else:
            with db.session_ctx() as sess:
                pt = time.time()

                lab = db.get_labnumber(ln)

                endtime = get_datetime().time()
                self.info('analysis finished at {}'.format(endtime))

                un = self.run_spec.username
                dbuser = db.get_user(un)
                if dbuser is None:
                    self.debug('user= {} does not existing. adding to database now'.format(un))
                    dbuser = db.add_user(un)

                a = db.add_analysis(lab,
                                    user=dbuser,
                                    uuid=self.uuid,
                                    endtime=endtime,
                                    aliquot=aliquot,
                                    # step=self.run_spec.step,
                                    increment=self.run_spec.increment,
                                    comment=self.run_spec.comment)
                sess.flush()
                experiment = db.get_experiment(self.experiment_identifier, key='id')
                if experiment is not None:
                    # added analysis to experiment
                    a.experiment_id = experiment.id
                else:
                    self.warning('no experiment found for {}'.format(self.experiment_identifier))

                # save measurement
                meas = self._save_measurement(db, a)
                # save extraction
                ext = self._db_extraction_id
                if ext is not None:
                    dbext = db.get_extraction(ext, key='id')
                    a.extraction_id = dbext.id
                    # save sensitivity info to extraction
                    self._save_sensitivity(dbext, meas)

                else:
                    self.debug('no extraction to associate with this run')

                self._save_spectrometer_info(db, meas)

                # add selected history
                db.add_selected_histories(a)
                # self._save_isotope_info(a, ss)
                self._save_isotope_data(db, a)

                # save ic factor
                self._save_detector_intercalibration(db, a)

                # save blanks
                self._save_blank_info(db, a)

                # save peak center
                self._save_peak_center(db, a, cp)

                # save monitor
                self._save_monitor_info(db, a)

                mem_log('post pychron save')

                pt = time.time() - pt
                self.debug('pychron save time= {:0.3f} '.format(pt))
                file_log(pt)

        if self.use_secondary_database:
            if not self.datahub.secondary_connect():
                # if not self.massspec_importer or not self.massspec_importer.db.connected:
                self.debug('Secondary database is not available')
            else:
                self.debug('saving post measurement to secondary database')
                # save to massspec
                mt = time.time()
                self._save_to_massspec(cp)
                self.debug('mass spec save time= {:0.3f}'.format(time.time() - mt))
                mem_log('post mass spec save')

                #clear is_peak hop flag
                # self.is_peak_hop = False
                # self.plot_panel.is_peak_hop = False
                # return True

    def _save_isotope_data(self, db, analysis):
        self.debug('saving isotopes')

        dbhist = db.add_fit_history(analysis,
                                    user=self.run_spec.username)

        for iso in self.arar_age.isotopes.itervalues():
            detname = iso.detector
            dbdet = db.get_detector(detname)
            if dbdet is None:
                dbdet = db.add_detector(detname)
                # db.sess.flush()

            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.sniff, 'sniff')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso, 'signal')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.baseline, 'baseline')

    def _save_signal_data(self, db, dbhist, analysis, dbdet, iso, m, kind):

        self.debug('saving data {} {} xs={}'.format(iso.name, kind, len(m.xs)))

        dbiso = db.add_isotope(analysis, iso.name, dbdet, kind=kind)

        data = ''.join([struct.pack('>ff', x, y) for x, y in zip(m.xs, m.ys)])
        db.add_signal(dbiso, data)

        add_result = kind in ('baseline', 'signal')

        # filter_outliers=dict(iterations=1,
        #                      std_dev=2, filter_outliers=True)
        filter_outliers = self.default_outlier_filtering
        if add_result:
            if m.fit:
                # add fit
                db.add_fit(dbhist, dbiso, fit=m.fit)

            m.set_filtering(filter_outliers)

            # add isotope result
            # print 'a',m.value, m.error, type(m.error), type(nan)
            v, e = float(m.value), float(m.error)
            v = 0 if math.isnan(v) or math.isinf(v) else v
            e = 0 if math.isnan(e) or math.isinf(e) else e

            db.add_isotope_result(dbiso,
                                  dbhist,
                                  signal_=v, signal_err=e)

    def _save_sensitivity(self, extraction, measurement):
        self.info('saving sensitivity')

        # get the lastest sensitivity entry for this spectrometr
        spec = measurement.mass_spectrometer
        if spec:
            sens = spec.sensitivities
            if sens:
                extraction.sensitivity = sens[-1]

    def _save_peak_center(self, db, analysis, cp):
        self.info('saving peakcenter')

        dm = self.data_manager
        with dm.open_table(cp, 'peak_center') as tab:
            if tab is not None:
                packed_xy = [struct.pack('<ff', r['time'], r['value']) for r in tab.iterrows()]
                points = ''.join(packed_xy)
                center = tab.attrs.center_dac
                pc = db.add_peak_center(
                    analysis,
                    center=float(center),
                    points=points)
                return pc

    def _save_measurement(self, db, analysis):
        self.info('saving measurement')

        meas = db.add_measurement(
            analysis,
            self.run_spec.analysis_type,
            self.run_spec.mass_spectrometer)
        script = db.add_script(self.measurement_name, self.measurement_blob)

        meas.script_id = script.id

        return meas

    def _save_extraction(self, db, analysis=None, loadtable=None, output_blob=None, response_blob=None):
        self.info('saving extraction')

        spec = self.run_spec

        self.debug('Saving extraction device {}'.format(spec.extract_device))

        d = dict(extract_device=spec.extract_device,
                 extract_value=spec.extract_value,
                 extract_duration=spec.duration,
                 cleanup_duration=spec.cleanup,
                 weight=spec.weight,
                 response_blob=response_blob or '',
                 output_blob=output_blob or '',
                 sensitivity_multiplier=self.sensitivity_multiplier,
                 is_degas=spec.labnumber == 'dg')

        self._assemble_extraction_parameters(d)

        ext = db.add_extraction(analysis, **d)

        exp = db.add_script(self.experiment_queue_name,
                            self.experiment_queue_blob)
        self.debug('Script id {}'.format(exp.id))
        ext.experiment_blob_id = exp.id

        if self.extraction_name:
            script = db.add_script(self.extraction_name,
                                   self.extraction_blob)
            ext.script_id = script.id

        for pi in self.positions:
            if isinstance(pi, tuple):
                if len(pi) > 1:

                    if len(pi) == 3:
                        dbpos = db.add_analysis_position(ext, x=pi[0], y=pi[1], z=pi[2])
                    else:
                        dbpos = db.add_analysis_position(ext, x=pi[0], y=pi[1])

            else:
                dbpos = db.add_analysis_position(ext, pi)

            if loadtable and dbpos:
                dbpos.load_identifier = loadtable.name

        return ext

    def _save_spectrometer_info(self, db, meas):
        self.info('saving spectrometer info')

        if self.spec_dict:
            db.add_spectrometer_parameters(meas, self.spec_dict)
            for det, deflection in self.defl_dict.iteritems():
                det = db.add_detector(det)
                db.add_deflection(meas, det, deflection)

    def _save_detector_intercalibration(self, db, analysis):
        self.info('saving detector intercalibration')
        if self.arar_age:
            history = None
            for det in self.active_detectors:
                det = det.name
                ic = self.arar_age.get_ic_factor(det)
                self.info('default ic_factor {}= {}'.format(det, ic))
                if det == 'CDD':
                    # save cdd_ic_factor so it can be exported to secondary db
                    self.cdd_ic_factor = ic
                    self.debug('default cdd_ic_factor={}'.format(ic))

                user = self.run_spec.username
                user = user if user else NULL_STR

                self.info('{} adding detector intercalibration history for {}'.format(user, self.runid))

                if history is None:
                    history = db.add_detector_intercalibration_history(analysis,
                                                                       user=user)
                    analysis.selected_histories.selected_detector_intercalibration = history

                uv, ue = ic.nominal_value, ic.std_dev
                db.add_detector_intercalibration(history, det,
                                                 user_value=float(uv),
                                                 user_error=float(ue))

    def _save_blank_info(self, db, analysis):
        self.info('saving blank info')
        self._save_history_info(db, analysis, 'blanks', self.previous_blanks)

    def _save_history_info(self, db, analysis, name, values):
        if not values:
            self.debug('no previous {} to save {}'.format(name, values))
            return
        if self.run_spec.analysis_type.startswith('blank') or \
                self.run_spec.analysis_type.startswith('background'):
            return

        user = self.run_spec.username
        user = user if user else '---'

        funchist = getattr(db, 'add_{}_history'.format(name))
        self.info('{} adding {} history for {}-{}'.format(user, name,
                                                          analysis.labnumber.identifier,
                                                          analysis.aliquot))
        history = funchist(analysis, user=user)

        setattr(analysis.selected_histories,
                'selected_{}'.format(name), history)

        func = getattr(db, 'add_{}'.format(name))
        for isotope, v in values.iteritems():
            uv = v.nominal_value
            ue = float(v.std_dev)
            func(history, user_value=uv, user_error=ue,
                 isotope=isotope)

    def _save_monitor_info(self, db, analysis):
        if self.monitor:
            self.info('saving monitor info')

            for ci in self.monitor.checks:
                data = ''.join([struct.pack('>ff', x, y) for x, y in ci.data])
                params = dict(name=ci.name,
                              parameter=ci.parameter, criterion=ci.criterion,
                              comparator=ci.comparator, tripped=ci.tripped,
                              data=data)

                db.add_monitor(analysis, **params)

    def _save_to_massspec(self, p):
        #dm = self.data_manager
        ms = self.datahub.secondarystore
        h = ms.db.host
        dn = ms.db.name
        self.info('saving to massspec database {}/{}'.format(h, dn))

        exp = self._export_spec_factory()
        self.secondary_database_fail = False
        if ms.add_analysis(exp):
            self.info('analysis added to mass spec database')
        else:
            self.secondary_database_fail = 'Could not save {} to Mass Spec database'.format(self.runid)

    def _export_spec_factory(self):
        # dc = self.collector
        # fb = dc.get_fit_block(-1, self.fits)

        # rs_name, rs_text = self._assemble_script_blob()
        rid = self.runid

        # blanks = self.get_previous_blanks()

        # dkeys = [d.name for d in self._active_detectors]
        # sf = dict(zip(dkeys, fb))
        # p = self._current_data_frame

        ic = self.arar_age.get_ic_factor('CDD')

        exp = ExportSpec(runid=rid,
                         runscript_name=self.runscript_name,
                         runscript_text=self.runscript_blob,
                         # signal_fits=sf,
                         mass_spectrometer=self.run_spec.mass_spectrometer.capitalize(),
                         # blanks=blanks,
                         # data_path=p,
                         isotopes=self.arar_age.isotopes,
                         # signal_intercepts=si,
                         # signal_intercepts=self._processed_signals_dict,
                         is_peak_hop=self.save_as_peak_hop,
                         ic_factor_v=float(nominal_value(ic)),
                         ic_factor_e=float(std_dev(ic)))
        exp.load_record(self.run_spec)

        return exp

    def _assemble_extraction_parameters(self, edict):
        spec = self.run_spec

        edict.update(beam_diameter=spec.beam_diameter,
                     pattern=spec.pattern,
                     ramp_duration=spec.ramp_duration,
                     ramp_rate=spec.ramp_rate)

    #===============================================================================
    # data writing
    #===============================================================================
    def save_peak_center_to_file(self, pc):
        dm = self.data_manager
        with dm.open_file(self._current_data_frame):
            tab = dm.new_table('/', 'peak_center')
            xs, ys = pc.graph.get_data(), pc.graph.get_data(axis=1)

            for xi, yi in zip(xs, ys):
                nrow = tab.row
                nrow['time'] = xi
                nrow['value'] = yi
                nrow.append()

            xs, ys, _mx, _my = pc.result
            attrs = tab.attrs
            attrs.low_dac = xs[0]
            attrs.center_dac = xs[1]
            attrs.high_dac = xs[2]

            attrs.low_signal = ys[0]
            attrs.center_signal = ys[1]
            attrs.high_signal = ys[2]
            tab.flush()

    def get_data_writer(self, grpname):
        def write_data(dets, x, keys, signals):
            dm = self.data_manager
            for det in dets:
                k = det.name
                try:
                    if k in keys:
                        #self.debug('get table {} /{}/{}'.format(k,grpname, det.isotope))
                        t = dm.get_table(k, '/{}/{}'.format(grpname, det.isotope))
                        nrow = t.row
                        #                        self.debug('x={}'.format(x))
                        nrow['time'] = x
                        nrow['value'] = signals[keys.index(k)]
                        nrow.append()
                        t.flush()
                except AttributeError, e:
                    self.debug('error: {} group:{} det:{} iso:{}'.format(e, grpname, k, det.isotope))

        return write_data

    def _set_table_attr(self, name, grp, attr, value):
        dm = self.data_manager
        tab = dm.get_table(name, grp)
        setattr(tab.attrs, attr, value)
        tab.flush()

    def build_tables(self, gn, detectors):
        dm = self.data_manager
        with dm.open_file(self._current_data_frame):
            dm.new_group(gn)
            for i, d in enumerate(detectors):
                iso = d.isotope
                name = d.name
                # self._save_isotopes.append((iso, name, gn))

                isogrp = dm.new_group(iso, parent='/{}'.format(gn))
                dm.new_table(isogrp, name)

    def build_peak_hop_tables(self, gn, hops):
        dm = self.data_manager

        with dm.open_file(self._current_data_frame):
            dm.new_group(gn)

            for iso, det in parse_hops(hops, ret='iso,det'):
                # self._save_isotopes.append((iso, det, gn))
                isogrp = dm.new_group(iso, parent='/{}'.format(gn))
                _t = dm.new_table(isogrp, det)
                self.debug('add group {} table {}'.format(iso, det))

    def _local_lab_db_factory(self):
        if self.local_lab_db:
            return self.local_lab_db
        path = os.path.join(paths.hidden_dir, 'local_lab.db')
        # name = '/Users/ross/Sandbox/local.db'
        ldb = LocalLabAdapter(path=path)
        ldb.connect()
        ldb.build_database()
        return ldb

    def _get_default_outlier_filtering(self):
        return dict(filter_outliers=self.filter_outliers, iterations=self.fo_iterations,
                    std_dev=self.fo_std_dev)

#============= EOF =============================================

