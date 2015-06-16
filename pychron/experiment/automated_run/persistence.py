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

from traits.api import Instance, Bool, Float, Str, \
    Interface, provides
# ============= standard library imports ========================
import binascii
import os
import struct
import time
import math
from uncertainties import nominal_value, std_dev
# ============= local library imports  ==========================
# from pychron.core.codetools.file_log import file_log
# from pychron.core.codetools.memory_usage import mem_log
from xlwt import Workbook
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.helpers.filetools import subdirize
from pychron.core.ui.preference_binding import bind_preference
from pychron.database.adapters.local_lab_adapter import LocalLabAdapter
from pychron.experiment.automated_run.hop_util import parse_hops

from pychron.loggable import Loggable
# from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.paths import paths
from pychron.processing.export.export_spec import MassSpecExportSpec
from pychron.pychron_constants import NULL_STR

DEBUG = False

class IPersiter(Interface):
    def post_extraction_save(self, rblob, oblob, snapshots):
        pass

    def pre_measurement_save(self):
        pass

    def post_measurement_save(self):
        pass

    def save_peak_center_to_file(self, pc):
        pass

    def set_persistence_spec(self, **kw):
        pass


@provides(IPersiter)
class BasePersister(Loggable):
    per_spec = Instance('pychron.experiment.automated_run.persistence_spec.PersistenceSpec', ())
    save_enabled = Bool(False)

    def set_persistence_spec(self, **kw):
        self.per_spec.trait_set(**kw)

    def pre_extraction_save(self):
        """
        set runtime and rundate
        """
        d = get_datetime()
        self.runtime = d.time()
        self.rundate = d.date()
        self.info('Analysis started at {}'.format(self.runtime))
        self._pre_extraction_save_hook()

    def _pre_extraction_save_hook(self):
        pass


def get_sheet(wb, name):
    i = 0
    while 1:
        try:
            sh = wb.get_sheet(i)
            if sh.name == name:
                return sh
        except IndexError:
            return
        i += 1


class ExcelPersister(BasePersister):
    data_manager = Instance('pychron.managers.data_managers.xls_data_manager.XLSDataManager', ())

    def post_extraction_save(self, rblob, oblob, snapshots):
        """
        save extraction blobs, loadtable, and snapshots to the primary db

        :param rblob: response blob. binary time, value. time versus measured output
        :param oblob: output blob. binary time, value. time versus requested output
        :param snapshots: list of snapshot paths
        """
        if DEBUG:
            self.debug('Not saving extraction to database')
            return

        self.info('post extraction save')
        wb = self._workbook
        sh = wb.add_sheet('Meta')

        rs = self.per_spec.run_spec
        for i, (tag, attr) in enumerate((('User', 'username'),
                                         ('AnalysisType', 'analysis_type'),
                                         ('UUID', 'uud'))):
            sh.write(i, 0, tag)
            sh.write(i, 1, getattr(rs, attr))

        sh.write(i+1, 0, 'Load')
        sh.write(i+1, 1, self.load_name)

    # def pre_measurement_save(self):
    #     """
    #     """
    #     self.info('pre measurement save')

    def post_measurement_save(self):
        if DEBUG:
            self.debug('Not measurement saving to xls')
            return

        self.info('post measurement save')
        wb = self._workbook

        path = os.path.join(paths.isotope_dir, '{}.xls'.format(self.per_spec.run_spec.runid))
        sh = wb.add_sheet('data')
        self._save_isotopes(sh)
        wb.save(path)

    def _save_isotopes(self, sh):
        for i,(k, iso) in enumerate(self.per_spec.arar_age.isotopes.items()):

            sh.write(0, i, '{} time'.format(k))
            sh.write(0, i+1, '{} intensity'.format(k))

            sh.write(0, i+2, '{} sniff time'.format(k))
            sh.write(0, i+3, '{} sniff intensity'.format(k))
            sh.write(0, i+4, '{} baseline time'.format(k))
            sh.write(0, i+5, '{} baseline intensity'.format(k))

            for j,x in enumerate(iso.xs):
                sh.write(j+1,i, x)
            for j,y in enumerate(iso.ys):
                sh.write(j+1,i+1, y)

            for j,x in enumerate(iso.sniff.xs):
                sh.write(j+1,i+2, x)
            for j,y in enumerate(iso.sniff.ys):
                sh.write(j+1,i+3, y)

            for j,x in enumerate(iso.baseline.xs):
                sh.write(j+1,i+4, x)
            for j,y in enumerate(iso.baseline.ys):
                sh.write(j+1,i+5, y)

    def save_peak_center_to_file(self, pc):
        wb = self._workbook
        sh = wb.add_sheet('PeakCenter')
        xs, ys = pc.graph.get_data(), pc.graph.get_data(axis=1)
        sh.write(0, 0, 'DAC (V)')
        sh.write(0, 1, 'Intensity (fA)')

        for i, xi in enumerate(xs):
            sh.write(i + 1, 0, xi)

        for i, yi in enumerate(ys):
            sh.write(i + 1, 1, yi)

        xs, ys, _mx, _my = pc.result
        sh.write(0, 3, 'DAC')
        sh.write(0, 4, 'Intensity')
        sh.write(1, 2, 'Low')
        sh.write(2, 2, 'Center')
        sh.write(3, 2, 'High')
        for i, xi in enumerate(xs):
            sh.write(i, 3, xi)
        for i, yi in enumerate(ys):
            sh.write(i, 4, yi)

    def _pre_extraction_save_hook(self):
        self._workbook = Workbook()


class AutomatedRunPersister(BasePersister):
    """
    Save automated run data to file and database(s)

    #. save meta data to the local_lab database. This keeps are local record of all analyses run on the local system
    #. save data to an HDF5 file using a ``H5DataManager``
    #. use the ``Datahub`` to save data to databases

    """
    local_lab_db = Instance(LocalLabAdapter)
    datahub = Instance('pychron.experiment.datahub.Datahub')

    data_manager = Instance('pychron.managers.data_managers.h5_data_manager.H5DataManager', ())

    secondary_database_fail = False
    use_secondary_database = True
    use_analysis_grouping = Bool(False)
    grouping_threshold = Float
    grouping_suffix = Str

    _db_extraction_id = None
    _temp_analysis_buffer = None
    _current_data_frame = None

    def __init__(self, *args, **kw):
        super(AutomatedRunPersister, self).__init__(*args, **kw)
        self.bind_preferences()
        self._temp_analysis_buffer = []

    def bind_preferences(self):
        """
        bind to application preferences
        """
        prefid = 'pychron.experiment'
        bind_preference(self, 'use_analysis_grouping', '{}.use_analysis_grouping'.format(prefid))
        bind_preference(self, 'grouping_threshold', '{}.grouping_threshold'.format(prefid))
        bind_preference(self, 'grouping_suffix', '{}.grouping_suffix'.format(prefid))

    # ===============================================================================
    # data writing
    # ===============================================================================
    def save_peak_center_to_file(self, pc):
        """
        save a peak center to file

        :param pc: ``PeakCenter``
        """
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
        """
        grpname should be a str such as "signal", "baseline",etc
        return a closure for writing the data

        :param grpname: str
        :return: function
        """

        def write_data(dets, x, keys, signals):
            # todo: test whether saving data to h5 in real time is expansive
            # self.unique_warning('NOT Writing data to H5 in real time')
            # return

            dm = self.data_manager
            for det in dets:
                k = det.name
                try:
                    if k in keys:
                        if grpname == 'baseline':
                            grp = '/{}'.format(grpname)
                        else:
                            grp = '/{}/{}'.format(grpname, det.isotope)
                        # self.debug('get table {} /{}/{}'.format(k,grpname, det.isotope))
                        # self.debug('get table {}/{}'.format(grp,k))
                        t = dm.get_table(k, grp)

                        nrow = t.row
                        nrow['time'] = x
                        nrow['value'] = signals[keys.index(k)]
                        nrow.append()
                        t.flush()
                except AttributeError, e:
                    self.debug('error: {} group:{} det:{} iso:{}'.format(e, grpname, k, det.isotope))

        return write_data

    def build_tables(self, grpname, detectors):
        """
        construct the hdf5 table structure

        :param grpname: str
        :param detectors: list
        """

        self.debug('build tables- {} {}'.format(grpname, detectors))
        dm = self.data_manager
        with dm.open_file(self._current_data_frame):
            dm.new_group(grpname)
            for i, d in enumerate(detectors):
                iso = d.isotope
                name = d.name
                if grpname == 'baseline':
                    dm.new_table('/{}'.format(grpname), name)
                    self.debug('add group {} table {}'.format(grpname, name))
                else:
                    isogrp = dm.new_group(iso, parent='/{}'.format(grpname))
                    dm.new_table(isogrp, name)
                    self.debug('add group {} table {}'.format(isogrp, name))

    def build_peak_hop_tables(self, grpname, hops):
        """
        construct the table structure for a peak hop
        hops needs to be a str parsable by ``parse_hops``

        :param grpname: str
        :param hops: str
        """
        dm = self.data_manager

        with dm.open_file(self._current_data_frame):
            dm.new_group(grpname)

            for iso, det, is_baseline in parse_hops(hops, ret='iso,det,is_baseline'):
                if is_baseline:
                    continue
                isogrp = dm.new_group(iso, parent='/{}'.format(grpname))
                dm.new_table(isogrp, det)
                self.debug('add group {} table {}'.format(isogrp, det))

    def get_last_aliquot(self, identifier):
        return self.datahub.get_greatest_aliquot(identifier)

    def writer_ctx(self):
        return self.data_manager.open_file(self._current_data_frame)

    # def pre_extraction_save(self):
    #     """
    #     set runtime and rundate
    #     """
    #     d = get_datetime()
    #     self.runtime = d.time()
    #     self.rundate = d.date()
    #     self.info('Analysis started at {}'.format(self.runtime))

    def post_extraction_save(self, rblob, oblob, snapshots):
        """
        save extraction blobs, loadtable, and snapshots to the primary db

        :param rblob: response blob. binary time, value. time versus measured output
        :param oblob: output blob. binary time, value. time versus requested output
        :param snapshots: list of snapshot paths
        """
        if DEBUG:
            self.debug('Not saving extraction to database')
            return
        self.info('post extraction save')

        db = self.datahub.mainstore.db
        if db:
            with db.session_ctx() as sess:
                loadtable = db.get_loadtable(self.per_spec.load_name)
                if loadtable is None:
                    loadtable = db.add_load(self.per_spec.load_name)

                ext = self._save_extraction(db, loadtable=loadtable,
                                            response_blob=rblob,
                                            output_blob=oblob,
                                            snapshots=snapshots)
                sess.commit()
                self._db_extraction_id = int(ext.id)
        else:
            self.debug('No database instance')

    def pre_measurement_save(self):
        """
        setup hdf5 file
        """
        self.info('pre measurement save')

        dm = self.data_manager
        # make a new frame for saving data

        name = self.per_spec.run_spec.uuid
        root, tail = subdirize(paths.isotope_dir, '{}.h5'.format(name))
        path = os.path.join(root, tail)
        # path = os.path.join(paths.isotope_dir, '{}.h5'.format(name))

        self._current_data_frame = path
        frame = dm.new_frame(path)

        attrs = frame.root._v_attrs
        attrs['USER'] = self.per_spec.run_spec.username
        attrs['ANALYSIS_TYPE'] = self.per_spec.run_spec.analysis_type

        dm.close_file()

    def post_measurement_save(self):
        """
        check for runid conflicts. automatically update runid if conflict

        #. save to primary database (aka mainstore)
        #. save detector_ic to csv if applicable
        #. save to secondary database
        """
        if DEBUG:
            self.debug('Not measurement saving to database')
            return

        self.info('post measurement save')
        if not self.save_enabled:
            self.info('Database saving disabled')
            return

        # check for conflicts immediately before saving
        # automatically update if there is an issue
        run_spec = self.per_spec.run_spec
        conflict = self.datahub.is_conflict(run_spec)
        if conflict:
            self.debug('post measurement datastore conflict found. Automatically updating the aliquot and step')
            self.datahub.update_spec(run_spec)

        cp = self._current_data_frame

        ln = run_spec.labnumber
        aliquot = run_spec.aliquot

        # save to local sqlite database for backup and reference
        # self._local_db_save()

        # save to a database
        db = self.datahub.mainstore.db
        if not db or not db.connected:
            self.warning('No database instanc. Not saving post measurement to primary database')
        else:
            with db.session_ctx() as sess:
                pt = time.time()

                lab = db.get_labnumber(ln)

                endtime = get_datetime().time()
                self.info('analysis finished at {}'.format(endtime))

                un = run_spec.username
                dbuser = db.get_user(un)
                if dbuser is None:
                    self.debug('user= {} does not existing. adding to database now'.format(un))
                    dbuser = db.add_user(un)

                self.debug('adding analysis identifier={}, aliquot={}, '
                           'step={}, increment={}'.format(ln, aliquot,
                                                          run_spec.step,
                                                          run_spec.increment))
                a = db.add_analysis(lab,
                                    user=dbuser,
                                    uuid=run_spec.uuid,
                                    endtime=endtime,
                                    aliquot=aliquot,
                                    step=run_spec.step,
                                    increment=run_spec.increment,
                                    comment=run_spec.comment,
                                    whiff_result=self.per_spec.whiff_result)
                sess.flush()
                run_spec.analysis_dbid = a.id
                run_spec.analysis_timestamp = a.analysis_timestamp

                experiment = db.get_experiment(self.per_spec.experiment_identifier, key='id')
                if experiment is not None:
                    # added analysis to experiment
                    a.experiment_id = experiment.id
                else:
                    self.warning('no experiment found for {}'.format(self.per_spec.experiment_identifier))

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

                # save gains
                self._save_gains(db, a)

                if self.use_analysis_grouping:
                    self._save_analysis_group(db, a)

                # mem_log('post pychron save')

                pt = time.time() - pt
                self.debug('pychron save time= {:0.3f} '.format(pt))
                # file_log(pt)

        self.debug('$$$$$$$$$$$$$$$ auto_save_detector_ic={}'.format(self.auto_save_detector_ic))
        if self.auto_save_detector_ic:
            try:
                self._save_detector_ic_csv()
            except BaseException, e:
                self.debug('Failed auto saving detector ic. {}'.format(e))

        # don't save detector_ic runs to mass spec
        # measurement of an isotope on multiple detectors likely possible with mass spec but at this point
        # not worth trying.
        if self.use_secondary_database:
            from pychron.experiment.datahub import check_secondary_database_save

            if check_secondary_database_save(ln):
                if not self.datahub.secondary_connect():
                    # if not self.massspec_importer or not self.massspec_importer.db.connected:
                    self.debug('Secondary database is not available')
                else:
                    self.debug('saving post measurement to secondary database')
                    # save to massspec
                    mt = time.time()
                    self._save_to_massspec(cp)
                    self.debug('mass spec save time= {:0.3f}'.format(time.time() - mt))
                    # mem_log('post mass spec save')

    # private
    def _save_detector_ic_csv(self):

        from pychron.experiment.utilities.detector_ic import make_items, save_csv
        from pychron.experiment.utilities.identifier import get_analysis_type

        if get_analysis_type(self.per_spec.run_spec.identifier) == 'detector_ic':
            items = make_items(self.per_spec.arar_age.isotopes)

            save_csv(self.per_spec.run_spec.record_id, items)

    def _save_gains(self, db, analysis):
        self.debug('saving gains')
        ha = db.make_gains_hash(self.per_spec.gains)
        dbhist = db.get_gain_history(ha)
        if not dbhist:
            dbhist = db.add_gain_history(ha, save_type='arun')
            for d, v in self.per_spec.gains.items():
                db.add_gain(d, v, dbhist)
            db.commit()

        analysis.gain_history_id = dbhist.id

    def _save_analysis_group(self, db, analysis):
        """
            if analysis is an unknown add to project's analysis_group
            if analysis_group does not exist make it

            if project is reference then find and associate with the unknown's project
            if the next analysis is not from the same project then need to associate this analysis
            with that project as well.
        """
        self.debug('save analysis_group')
        rs = self.per_spec.run_spec
        prj = rs.project
        if prj == 'references':
            # get the most recent unknown analysis
            lan = db.get_last_analysis(spectrometer=rs.mass_spectrometer,
                                       analysis_type=rs.analysis_type,
                                       hours_limit=self.grouping_threshold)
            if lan is not None:
                try:
                    # prj = lan.labnumber.sample.project.name
                    prj = lan.project_name
                    self._add_to_project_group(db, prj, analysis)

                    # add this analysis to a temporary buffer. this is used when a following
                    # analysis is associated with a different project
                    self._temp_analysis_buffer.append((prj, analysis.uuid))

                except AttributeError:
                    pass
            else:
                # this maybe the first reference in the queue, so it should be associated with
                # the first subsequent unknown.
                self._temp_analysis_buffer.append((None, analysis.uuid))

        else:
            self._add_to_project_group(db, prj, analysis)

            if self._temp_analysis_buffer:
                for p, uuid in self._temp_analysis_buffer:
                    if p != prj:
                        analysis = db.get_analysis_uuid(uuid)
                        self._add_to_project_group(db, prj, analysis)

            self._temp_analysis_buffer = []

    def _add_to_project_group(self, db, prj, analysis):
        if self.grouping_suffix:
            prj = '{}-{}'.format(prj, self.grouping_suffix)

        ag = db.get_analysis_group(prj, key='name')
        if ag is None:
            ag = db.add_analysis_group(prj)

        # modify ag's id to reflect addition of another analysis
        aa = ag.analyses[:]
        aa.append(analysis)
        ag.id = binascii.crc32(''.join([ai.uuid for ai in aa]))

        db.add_analysis_group_set(ag, analysis)

    def _save_isotope_data(self, db, analysis):
        self.debug('saving isotopes')

        dbhist = db.add_fit_history(analysis,
                                    user=self.per_spec.run_spec.username)

        for iso in self.per_spec.arar_age.isotopes.itervalues():
            detname = iso.detector
            dbdet = db.get_detector(detname)
            if dbdet is None:
                dbdet = db.add_detector(detname)
                # db.sess.flush()

            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.sniff, 'sniff')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso, 'signal')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.baseline, 'baseline')

    def _get_filter_outlier_dict(self, iso, kind):
        if kind == 'baseline':
            fods = self.per_spec.baseline_fods
            key = iso.detector
        else:
            fods = self.per_spec.signal_fods
            key = iso.name

        try:
            fod = fods[key]
        except KeyError:
            fod = {'filter_outliers': False, 'iterations': 1, 'std_devs': 2}
        return fod

    def _save_signal_data(self, db, dbhist, analysis, dbdet, iso, m, kind):
        if not (len(m.xs) and len(m.ys)):
            self.debug('no data for {} {}'.format(iso.name, kind))
            return

        self.debug('saving data {} {} xs={}'.format(iso.name, kind, len(m.xs)))
        dbiso = db.add_isotope(analysis, iso.name, dbdet, kind=kind)
        data = ''.join([struct.pack('>ff', x, y) for x, y in zip(m.xs, m.ys)])
        db.add_signal(dbiso, data)

        add_result = kind in ('baseline', 'signal')

        if add_result:
            fod = self._get_filter_outlier_dict(iso, kind)
            m.set_filtering(fod)
            if m.fit:
                # add fit
                db.add_fit(dbhist, dbiso,
                           fit=m.fit,
                           filter_outliers=fod.get('filter_outliers', False),
                           filter_outlier_iterations=fod.get('iterations', 1),
                           filter_outlier_std_devs=fod.get('std_devs', 2))

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

        spec = self.per_spec.run_spec
        meas = db.add_measurement(
            analysis,
            spec.analysis_type,
            spec.mass_spectrometer,
            time_zero_offset=spec.collection_time_zero_offset)

        script = db.add_script(self.per_spec.measurement_name, self.per_spec.measurement_blob)

        meas.script_id = script.id

        return meas

    def _save_extraction(self, db, analysis=None, loadtable=None,
                         output_blob=None, response_blob=None, snapshots=None):
        """
            snapshots: list of tuples, (local_path, remote_path, imageblob)
        """
        self.info('saving extraction')

        spec = self.per_spec.run_spec

        self.debug('Saving extraction device {}'.format(spec.extract_device))

        d = dict(extract_device=spec.extract_device,
                 extract_value=spec.extract_value,
                 extract_duration=spec.duration,
                 cleanup_duration=spec.cleanup,
                 weight=spec.weight,
                 response_blob=response_blob or '',
                 output_blob=output_blob or '',
                 sensitivity_multiplier=self.per_spec.sensitivity_multiplier,
                 is_degas=spec.labnumber == 'dg')

        self._assemble_extraction_parameters(d)

        ext = db.add_extraction(analysis, **d)

        exp = db.add_script(self.per_spec.experiment_queue_name,
                            self.per_spec.experiment_queue_blob)
        self.debug('Script id {}'.format(exp.id))
        ext.experiment_blob_id = exp.id

        if self.per_spec.extraction_name:
            script = db.add_script(self.per_spec.extraction_name,
                                   self.per_spec.extraction_blob)
            ext.script_id = script.id

        for i, pp in enumerate(self.per_spec.positions):
            if isinstance(pp, tuple):
                if len(pp) > 1:

                    if len(pp) == 3:
                        dbpos = db.add_analysis_position(ext, x=pp[0], y=pp[1], z=pp[2])
                    else:
                        dbpos = db.add_analysis_position(ext, x=pp[0], y=pp[1])

            else:
                dbpos = db.add_analysis_position(ext, pp)
                try:
                    ep = self.extraction_positions[i]
                    dbpos.x = ep[0]
                    dbpos.y = ep[1]
                    if len(ep) == 3:
                        dbpos.z = ep[2]
                except IndexError:
                    self.debug('no extraction position for {}'.format(pp))

            if loadtable and dbpos:
                dbpos.load_identifier = loadtable.name

        if snapshots:
            for lpath, rpath, image in snapshots:
                dbsnap = self.db.add_snapshot(lpath, remote_path=rpath,
                                              image=image)
                ext.snapshots.append(dbsnap)
        return ext

    def _save_spectrometer_info(self, db, meas):
        self.info('saving spectrometer info')

        if self.per_spec.spec_dict:
            db.add_spectrometer_parameters(meas, self.per_spec.spec_dict)
            for det, deflection in self.defl_dict.iteritems():
                det = db.add_detector(det)
                db.add_deflection(meas, det, deflection)

    def _save_detector_intercalibration(self, db, analysis):
        self.info('saving detector intercalibration')
        if self.per_spec.arar_age:
            history = None
            for det in self.per_spec.active_detectors:
                det = det.name
                ic = self.per_spec.arar_age.get_ic_factor(det)
                self.info('default ic_factor {}= {}'.format(det, ic))
                if det == 'CDD':
                    # save cdd_ic_factor so it can be exported to secondary db
                    self.cdd_ic_factor = ic
                    self.debug('default cdd_ic_factor={}'.format(ic))

                user = self.per_spec.run_spec.username
                user = user if user else NULL_STR

                self.info('{} adding detector intercalibration history for {}'.format(user, self.per_spec.run_spec.runid))

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
        self.debug('preceding blank id={}'.format(self.per_spec.previous_blank_id))

        self._save_history_info(db, analysis, 'blanks', self.per_spec.previous_blanks,
                                preceding_id=self.per_spec.previous_blank_id)

    def _save_history_info(self, db, analysis, name, values, preceding_id=None):
        if not values:
            self.debug('no previous {} to save {}'.format(name, values))
            return
        spec = self.per_spec.run_spec
        if spec.analysis_type.startswith('blank') or \
                spec.analysis_type.startswith('background'):
            return

        user = spec.username
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
            if preceding_id:
                func(history, user_value=uv, user_error=ue,
                     isotope=isotope, preceding_id=preceding_id)
            else:
                func(history, user_value=uv, user_error=ue,
                     isotope=isotope)

    def _save_monitor_info(self, db, analysis):
        if self.per_spec.monitor:
            self.info('saving monitor info')

            for ci in self.per_spec.monitor.checks:
                data = ''.join([struct.pack('>ff', x, y) for x, y in ci.data])
                params = dict(name=ci.name,
                              parameter=ci.parameter, criterion=ci.criterion,
                              comparator=ci.comparator, tripped=ci.tripped,
                              data=data)

                db.add_monitor(analysis, **params)

    def _save_to_massspec(self, p):
        # dm = self.data_manager
        ms = self.datahub.secondarystore
        h = ms.db.host
        dn = ms.db.name
        self.info('saving to massspec database {}/{}'.format(h, dn))

        exp = self._export_spec_factory()
        self.secondary_database_fail = False
        if ms.add_analysis(exp):
            self.info('analysis added to mass spec database')
        else:
            self.secondary_database_fail = 'Could not save {} to Mass Spec database'.format(self.per_spec.run_spec.runid)

    def _export_spec_factory(self):
        # dc = self.collector
        # fb = dc.get_fit_block(-1, self.fits)

        # rs_name, rs_text = self._assemble_script_blob()
        rid = self.per_spec.run_spec.runid

        # blanks = self.get_previous_blanks()

        # dkeys = [d.name for d in self._active_detectors]
        # sf = dict(zip(dkeys, fb))
        # p = self._current_data_frame

        ic = self.per_spec.arar_age.get_ic_factor('CDD')

        exp = MassSpecExportSpec(runid=rid,
                                 runscript_name=self.per_spec.runscript_name,
                                 runscript_text=self.per_spec.runscript_blob,
                                 # signal_fits=sf,
                                 mass_spectrometer=self.per_spec.run_spec.mass_spectrometer.capitalize(),
                                 # blanks=blanks,
                                 # data_path=p,
                                 isotopes=self.per_spec.arar_age.isotopes,
                                 # signal_intercepts=si,
                                 # signal_intercepts=self._processed_signals_dict,
                                 is_peak_hop=self.per_spec.save_as_peak_hop,
                                 ic_factor_v=float(nominal_value(ic)),
                                 ic_factor_e=float(std_dev(ic)))
        exp.load_record(self.per_spec.run_spec)

        return exp

    def _assemble_extraction_parameters(self, edict):
        spec = self.per_spec.run_spec

        edict.update(beam_diameter=spec.beam_diameter or 0,
                     pattern=spec.pattern,
                     ramp_duration=spec.ramp_duration or 0,
                     ramp_rate=spec.ramp_rate or 0)

    def _set_table_attr(self, name, grp, attr, value):
        dm = self.data_manager
        tab = dm.get_table(name, grp)
        setattr(tab.attrs, attr, value)
        tab.flush()

    def _local_db_save(self):
        ldb = self._local_lab_db_factory()
        with ldb.session_ctx():

            spec = self.per_spec.run_spec
            ln = spec.labnumber
            aliquot = spec.aliquot
            step = spec.step
            uuid = spec.uuid
            cp = self._current_data_frame

            ldb.add_analysis(labnumber=ln,
                             aliquot=aliquot,
                             uuid=uuid,
                             step=step,
                             collection_path=cp)

    def _local_lab_db_factory(self):
        if self.local_lab_db:
            return self.local_lab_db
        path = os.path.join(paths.hidden_dir, 'local_lab.db')
        # name = '/Users/ross/Sandbox/local.db'
        ldb = LocalLabAdapter(path=path)
        ldb.connect()
        ldb.build_database()
        return ldb

        # def _get_default_outlier_filtering(self):
        # return dict(filter_outliers=self.filter_outliers, iterations=self.fo_iterations,
        # std_dev=self.fo_std_dev)

# ============= EOF =============================================

