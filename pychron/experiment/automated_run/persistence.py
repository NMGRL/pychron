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
from traits.api import Instance, Bool, Interface, provides, Long, Str, Float
# ============= standard library imports ========================
import binascii
import time
import os
from xlwt import Workbook
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.helpers.filetools import subdirize
from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.preference_binding import set_preference
from pychron.experiment.automated_run.hop_util import parse_hops

from pychron.loggable import Loggable
# from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.paths import paths

DEBUG = False


class IPersister(Interface):
    def post_extraction_save(self):
        pass

    def pre_measurement_save(self):
        pass

    def post_measurement_save(self, **kw):
        pass

    def save_peak_center_to_file(self, pc):
        pass

    def set_persistence_spec(self, **kw):
        pass


@provides(IPersister)
class BasePersister(Loggable):
    per_spec = Instance('pychron.experiment.automated_run.persistence_spec.PersistenceSpec', ())
    save_enabled = Bool(False)

    def post_extraction_save(self):
        pass

    def pre_measurement_save(self):
        pass

    def post_measurement_save(self, **kw):
        self._post_measurement_save(**kw)

    def save_peak_center_to_file(self, pc):
        self._save_peak_center(pc)

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

    def post_extraction_save(self):
        """
        save extraction blobs, loadtable, and snapshots to the primary db

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

        sh.write(i + 1, 0, 'Load')
        sh.write(i + 1, 1, self.load_name)

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
        for i, (k, iso) in enumerate(self.per_spec.isotope_group.isotopes.items()):

            sh.write(0, i, '{} time'.format(k))
            sh.write(0, i + 1, '{} intensity'.format(k))

            sh.write(0, i + 2, '{} sniff time'.format(k))
            sh.write(0, i + 3, '{} sniff intensity'.format(k))
            sh.write(0, i + 4, '{} baseline time'.format(k))
            sh.write(0, i + 5, '{} baseline intensity'.format(k))

            for j, x in enumerate(iso.xs):
                sh.write(j + 1, i, x)
            for j, y in enumerate(iso.ys):
                sh.write(j + 1, i + 1, y)

            for j, x in enumerate(iso.sniff.xs):
                sh.write(j + 1, i + 2, x)
            for j, y in enumerate(iso.sniff.ys):
                sh.write(j + 1, i + 3, y)

            for j, x in enumerate(iso.baseline.xs):
                sh.write(j + 1, i + 4, x)
            for j, y in enumerate(iso.baseline.ys):
                sh.write(j + 1, i + 5, y)

    def _save_peak_center(self, pc):
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
    dbexperiment_identifier = Long
    # local_lab_db = Instance(LocalLabAdapter)
    datahub = Instance('pychron.experiment.datahub.Datahub')

    data_manager = Instance('pychron.managers.data_managers.h5_data_manager.H5DataManager', ())

    secondary_database_fail = False
    use_massspec_database = True
    use_analysis_grouping = Bool(False)
    grouping_threshold = Float
    grouping_suffix = Str

    _db_extraction_id = None
    _temp_analysis_buffer = None
    _current_data_frame = None

    def __init__(self, *args, **kw):
        super(AutomatedRunPersister, self).__init__(*args, **kw)
        # self.bind_preferences()
        self._temp_analysis_buffer = []

    def set_preferences(self, preferences):
        """
        bind to application preferences
        """
        # prefid = 'pychron.experiment'
        # bind_preference(self, 'use_analysis_grouping', '{}.use_analysis_grouping'.format(prefid))
        # bind_preference(self, 'grouping_threshold', '{}.grouping_threshold'.format(prefid))
        # bind_preference(self, 'grouping_suffix', '{}.grouping_suffix'.format(prefid))
        self.debug('set preferences')

        for attr, cast in (('use_analysis_grouping', to_bool),
                           ('grouping_threshold', float),
                           ('grouping_suffix', str)):
            set_preference(preferences, self, attr, 'pychron.experiment.{}'.format(attr), cast)

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

            dm.new_group('peak_centers')
            for result in pc.get_results():
                tab = dm.new_table('/peak_centers', result.detector)
                for x, y in result.points:
                    nrow = tab.row
                    nrow['time'] = x
                    nrow['value'] = y
                    nrow.append()

                attrs = tab.attrs
                for a in result.attrs:
                    setattr(attrs, a, getattr(result, a))

                tab.flush()

    def get_data_writer(self, grpname):
        """
        grpname should be a str such as "signal", "baseline",etc
        return a closure for writing the data

        :param grpname: str
        :return: function
        """
        tables = {}

        def write_data(dets, x, keys, signals):
            # todo: test whether saving data to h5 in real time is expansive

            # disable H5 data writer
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

                        tag = '{}/{}'.format(grp, k)
                        if tag in tables:
                            t = tables['tag']
                        else:
                            t = dm.get_table(k, grp)

                        nrow = t.row
                        nrow['time'] = x
                        nrow['value'] = signals[keys.index(k)]
                        nrow.append()
                        t.flush()
                except AttributeError, e:
                    self.debug('error: {} group:{} det:{} iso:{}'.format(e, grpname, k, det.isotope))

        return write_data

    def build_tables(self, grpname, detectors, n):
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
                    dm.new_table('/{}'.format(grpname), name, n)
                    self.debug('add group {} table {}'.format(grpname, name))
                else:
                    isogrp = dm.new_group(iso, parent='/{}'.format(grpname))
                    dm.new_table(isogrp, name, n)
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

    def post_extraction_save(self):
        """
        save extraction blobs, loadtable, and snapshots to the primary db
        """
        self.debug('AutomatedRunPersister post_extraction_save deprecated')
        return

        if DEBUG:
            self.debug('Not saving extraction to database')
            return
        self.info('post extraction save')

        db = self.datahub.get_db('isotopedb')
        if db:
            with db.session_ctx() as sess:
                loadtable = db.get_loadtable(self.per_spec.load_name)
                if loadtable is None:
                    loadtable = db.add_load(self.per_spec.load_name, 'None')

                ext = self._save_extraction(db, loadtable=loadtable,
                                            response_blob=self.per_spec.response_blob,
                                            output_blob=self.per_spec.output_blob,
                                            snapshots=self.per_spec.snapshots)
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
        root, tail = subdirize(paths.isotope_dir, '{}.h5'.format(name), mode='w')
        path = os.path.join(root, tail)
        # path = os.path.join(paths.isotope_dir, '{}.h5'.format(name))

        self._current_data_frame = path
        frame = dm.new_frame(path)

        attrs = frame.root._v_attrs
        attrs['USER'] = self.per_spec.run_spec.username
        attrs['ANALYSIS_TYPE'] = self.per_spec.run_spec.analysis_type

        dm.close_file()

    def post_measurement_save(self, save_local=True):
        """
        check for runid conflicts. automatically update runid if conflict

        #. save to primary database (aka mainstore)
        #. save detector_ic to csv if applicable
        #. save to secondary database
        """
        # self.debug('AutomatedRunPersister post_measurement_save deprecated')
        # return

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

        # conflict = self.datahub.is_conflict(run_spec)
        # if conflict:
        #     self.debug('post measurement datastore conflict found. Automatically updating the aliquot and step')
        #     self.datahub.update_spec(run_spec)

        cp = self._current_data_frame

        ln = run_spec.labnumber
        aliquot = run_spec.aliquot

        if save_local:
            # save to local sqlite database for backup and reference
            self._local_db_save()

        # save to a database
        db = self.datahub.get_db('isotopedb')
        if not db or not db.connected:
            self.warning('No database instance. Not saving post measurement to isotopedb database')
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

                experiment = db.get_experiment(self.dbexperiment_identifier, key='id')
                if experiment is not None:
                    # added analysis to experiment
                    a.experiment_id = experiment.id
                else:
                    self.warning('no experiment found for {}'.format(self.dbexperiment_identifier))

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

        self.debug('$$$$$$$$$$$$$$$ auto_save_detector_ic={}'.format(self.per_spec.auto_save_detector_ic))
        if self.per_spec.auto_save_detector_ic:
            try:
                self._save_detector_ic_csv()
            except BaseException, e:
                self.debug('Failed auto saving detector ic. {}'.format(e))

        # don't save detector_ic runs to mass spec
        # measurement of an isotope on multiple detectors likely possible with mass spec but at this point
        # not worth trying.
        # if self.use_secondary_database:
        if self.use_massspec_database:
            from pychron.experiment.datahub import check_massspec_database_save

            if check_massspec_database_save(ln):
                if not self.datahub.store_connect('massspec'):
                    # if not self.massspec_importer or not self.massspec_importer.db.connected:
                    self.debug('Mass Spec database is not available')
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
            items = make_items(self.per_spec.isotope_group.isotopes)

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

        for iso in self.per_spec.isotope_group.isotopes.itervalues():
            detname = iso.detector
            dbdet = db.get_detector(detname)
            if dbdet is None:
                dbdet = db.add_detector(detname)
                # db.sess.flush()

            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.sniff, 'sniff')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso, 'signal')
            self._save_signal_data(db, dbhist, analysis, dbdet, iso, iso.baseline, 'baseline')
