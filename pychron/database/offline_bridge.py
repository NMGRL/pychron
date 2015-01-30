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
# from pychron.core.ui import set_toolkit
# set_toolkit('qt4')
# ============= enthought library imports =======================
from collections import defaultdict
import os

from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from traits.api import Any

# ============= standard library imports ========================
# ============= local library imports  ==========================
from sqlalchemy.orm.exc import NoResultFound
from pychron.core.helpers.logger_setup import wrap
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.orms.isotope.util import Base
from pychron.loggable import Loggable
from pychron.paths import paths


def quick_mapper(table):
    Base = declarative_base()

    class GenericMapper(Base):
        __table__ = table

    return GenericMapper


class DatabaseBridge(Loggable):
    kind = 'sqlite'
    # def init(self, p=None):
    #
    # #create a default db
    #     if p is None:
    #         p = os.path.join(paths.hidden_dir, 'data.db')
    #
    #     self.debug('init database {}'.format(p))
    #     self.path = p
    #     self.connect()
    #     if not os.path.isfile(p):
    #         self.debug('init creating all tables')
    #         metadata = Base.metadata
    #         self.create_all(metadata)
    source = Any
    dest = Any

    def add_analyses(self, ans):
        self.debug('adding analyses')
        self.debug('source={}'.format(self.source.url))
        self.debug('dest={}'.format(self.dest.url))
        self.dest.connect()

        db = self.source
        with self.dest.session_ctx() as dest:
            for ai in ans:
                self._add_analysis(ai, dest, db)
                # if not self.get_analysis_uuid(ai.uuid):
                # if progress:
                #     progress.change_message('Transfering analysis {}'.format(ai.record_id))

    def _add_analysis(self, ai, dest, db):
        src = db.sess
        ln = ai.labnumber
        if ln:
            # self.debug('copying analysis {}'.format(ai.record_id))
            #get the source objects
            ai = db.get_analysis_uuid(ai.uuid)
            ln = db.get_labnumber(ln)

            self._copy_table(dest, src, ln.irradiation_position.level.holder_id, 'irrad_holdertable')
            self._copy_table(dest, src, ln.irradiation_position.level.production_id,
                             'irrad_productiontable')
            self._copy_table(dest, src, ln.irradiation_position.level.irradiation.irradiation_chronology_id,
                             'irrad_chronologytable')
            self._copy_table(dest, src, ln.irradiation_position.level.irradiation_id,
                             'irrad_irradiationtable')

            self._copy_table(dest, src, ln.irradiation_position.level_id, 'irrad_leveltable')
            self._copy_table(dest, src, ln.irradiation_id, 'irrad_positiontable')

            sample = ln.sample
            if sample:
                self._copy_table(dest, src, sample.project_id, 'gen_projecttable')
                self._copy_table(dest, src, sample.material_id, 'gen_materialtable')
                self._copy_table(dest, src, ln.sample_id, 'gen_sampletable')

            self._copy_table(dest, src, ln.selected_flux_history.id, 'flux_HistoryTable')
            self._copy_table(dest, src, ln.selected_flux_history.flux.id, 'flux_FluxTable')
            if ln.selected_interpreted_age:
                self._copy_table(dest, src, ln.selected_interpreted_age.id, 'proc_InterpretedAgeHistoryTable')
                self._copy_table(dest, src, ln.selected_interpreted_age.interpreted_age.id, 'proc_InterpretedAgeTable')

            self._copy_table(dest, src, ai.lab_id, 'gen_labtable')

            self._copy_table(dest, src, ai.measurement.mass_spectrometer_id, 'gen_massspectrometertable')
            self._copy_table(dest, src, ai.measurement.analysis_type_id, 'gen_analysistypetable')
            self._copy_table(dest, src, ai.extraction.extract_device_id, 'gen_extractiondevicetable')
            self._copy_table(dest, src, ai.import_id, 'gen_importtable')
            self._copy_table(dest, src, ai.tag, 'proc_tagtable', attr='name')
            self._copy_table(dest, src, ai.measurement_id, 'meas_measurementtable')

            self._copy_table(dest, src, ai.extraction_id, 'meas_extractiontable')
            self._copy_table(dest, src, ai.id, 'meas_analysistable')

            for iso in ai.isotopes:
                self._copy_table(dest, src, iso.molecular_weight_id, 'gen_molecularweighttable')
                self._copy_table(dest, src, iso.detector_id, 'gen_detectortable')
                self._copy_table(dest, src, iso.id, 'meas_isotopetable')
                self._copy_table(dest, src, iso.signal.id, 'meas_signaltable')

            self._copy_table(dest, src, ai.selected_histories.selected_blanks.id, 'proc_BlanksHistoryTable')
            for bi in ai.selected_histories.selected_blanks.blanks:
                self._copy_table(dest, src, bi.id, 'proc_BlanksTable')

            self._copy_table(dest, src, ai.selected_histories.selected_fits.id, 'proc_FitHistoryTable')
            for bi in ai.selected_histories.selected_fits.fits:
                self._copy_table(dest, src, bi.id, 'proc_FitTable')

            self._copy_table(dest, src, ai.selected_histories.selected_detector_param.id,
                             'proc_DetectorParamHistoryTable')
            for bi in ai.selected_histories.selected_detector_param.detector_params:
                self._copy_table(dest, src, bi.id, 'proc_DetectorParamTable')

            if ai.selected_histories.selected_detector_intercalibration is not None:
                self._copy_table(dest, src, ai.selected_histories.selected_detector_intercalibration.id,
                                 'proc_DetectorIntercalibrationHistoryTable')
                for bi in ai.selected_histories.selected_detector_intercalibration.detector_intercalibrations:
                    self._copy_table(dest, src, bi.id, 'proc_DetectorIntercalibrationTable')

            self._copy_table(dest, src, ai.selected_histories.id, 'proc_selectedhistoriestable')
            dest.commit()

    def _copy_table(self, dest, src, pid, tn, verbose=True, attr='id'):
        meta = Base.metadata
        meta.bind = dest.bind
        dtable = Table(tn, meta, autoload=True)
        dq = dest.query(dtable)

        dq = dq.filter(getattr(dtable.c, attr) == pid)

        try:
            if dq.one():
                return
        except NoResultFound:
            meta.bind = src.bind

            table = Table(tn, meta, autoload=True)
            nrec = quick_mapper(table)
            columns = table.columns.keys()

            if verbose:
                msg = 'Transferring records {}'.format(tn)
                if verbose == 1:
                    cols = wrap(columns)
                    msg = '{} {}'.format(msg, 'Columns={}'.format(tn, cols))

                self.debug(msg)

                q = src.query(table)
                q = q.filter(getattr(table.c, attr) == pid)
            try:

                record = q.one()
                data = dict([(str(column), getattr(record, column)) for column in columns])
                dest.merge(nrec(**data))
            except NoResultFound:
                pass
            finally:
                dest.flush()


class OfflineBridge(IsotopeAdapter):
    """
        use to gather data from mysql and save to sqlite
    """
    kind = 'sqlite'
    _cache = None
    _table_cache = None
    _src_table_cache = None

    def init(self, p=None, overwrite=False):
        self._table_cache = dict()
        self._src_table_cache = dict()

        self._cache = defaultdict(list)

        # create a default db
        if p is None:
            p = os.path.join(paths.hidden_dir, 'data.db')

        if overwrite and os.path.isfile(p):
            os.remove(p)

        self.debug('init database {}'.format(p))
        self.path = p
        self.connect()
        if not os.path.isfile(p):
            self.debug('init creating all tables')
            metadata = Base.metadata
            self.create_all(metadata)

    def _copy(self, dban, ln, dest, src):
        # get the source objects
        self._copy_table(dest, src, dban.id, 'meas_analysistable')
        self._copy_table(dest, src, dban.lab_id, 'gen_labtable')
        self._copy_table(dest, src, dban.extraction_id, 'meas_extractiontable')
        self._copy_table(dest, src, dban.measurement_id, 'meas_measurementtable')
        self._copy_table(dest, src, dban.measurement.analysis_type_id, 'gen_analysistypetable')
        self._copy_table(dest, src, dban.measurement.mass_spectrometer_id, 'gen_massspectrometertable')
        self._copy_table(dest, src, dban.selected_histories.id, 'proc_selectedhistoriestable')
        self._copy_table(dest, src, dban.tag, 'proc_tagtable', primary_key='name')
        for fi in dban.fit_histories:
            self._copy_table(dest, src, fi.id, 'proc_fithistorytable')
            for fit in fi.fits:
                self._copy_table(dest, src, fit.id, 'proc_fittable')

        for bhist in dban.blanks_histories:
            self._copy_table(dest, src, bhist.id, 'proc_blankshistorytable')
            for blank in bhist.blanks:
                self._copy_table(dest, src, blank.id, 'proc_blankstable')
                for aset in blank.analysis_set:
                    self._copy_table(dest, src, aset.id, 'proc_blankssettable')
                for vset in blank.value_set:
                    self._copy_table(dest, src, vset.id, 'proc_BlanksSetValueTable')

        for iso in dban.isotopes:
            self._copy_table(dest, src, iso.id, 'meas_isotopetable')
            self._copy_table(dest, src, iso.detector_id, 'gen_detectortable')
            self._copy_table(dest, src, iso.molecular_weight_id, 'gen_molecularweighttable')
            for result in iso.results:
                self._copy_table(dest, src, result.id, 'proc_IsotopeResultsTable')

            dest.flush()

        self._copy_table(dest, src, ln.sample_id, 'gen_sampletable')
        sample = ln.sample
        if sample:
            self._copy_table(dest, src, sample.project_id, 'gen_projecttable')
            self._copy_table(dest, src, sample.material_id, 'gen_materialtable')

        self._copy_table(dest, src, ln.irradiation_id, 'irrad_positiontable')
        self._copy_table(dest, src, ln.irradiation_position.level_id, 'irrad_leveltable')
        self._copy_table(dest, src, ln.irradiation_position.level.irradiation_id,
                         'irrad_irradiationtable')
        self._copy_table(dest, src, ln.irradiation_position.level.production_id,
                         'irrad_productiontable')

        for fhist in ln.irradiation_position.flux_histories:
            self._copy_table(dest, src, fhist.id, 'flux_historytable')
            self._copy_table(dest, src, fhist.flux.id, 'flux_fluxtable')

        dest.flush()

    def add_analyses(self, db, ans, progress):
        self.debug('adding analyses')
        self.debug('source={}'.format(db.url))
        self.debug('dest={}'.format(self.path))
        self.connect()

        src = db.sess
        with self.session_ctx() as dest:
            import time
            times = []
            for ai in ans:
                st = time.time()
                if not self.get_analysis_uuid(ai.uuid):
                    if progress:
                        progress.change_message('Transfering analysis {}'.format(ai.record_id))

                    ln = ai.labnumber
                    if not ln:
                        self.warning('not copying meas_AnalysisTable.id={}. no labnumber'.format(ai.id))
                        continue

                    dban = db.get_analysis_uuid(ai.uuid)
                    ln = db.get_labnumber(ln)

                    self.debug('copying analysis {}'.format(ai.record_id))
                    self._copy(dban, ln, dest, src)
                times.append(time.time()-st)
            print times, sum(times)/len(times)

    def _copy_table(self, dest, src, pid, tn, primary_key='id', verbose=False):

        """
            cache rows added
        """

        # added_ids = self._cache[tn]
        # # print tn, pid, added_ids, pid in added_ids
        # if pid in added_ids:
        #     print 'skipping', pid, tn
        #     return
        # else:
        #     added_ids.append(pid)

        meta = Base.metadata
        meta.bind = dest.bind

        dtable = Table(tn, meta, autoload=True)
        # dtable = self._table_cache.get(tn)
        # if dtable is None:
        #     dtable = Table(tn, meta, autoload=True)
        #     self._table_cache[tn] = dtable
        # else:
        #     print 'using cache {}'.format(tn)

        dq = dest.query(dtable)
        dq = dq.filter(getattr(dtable.c, primary_key) == pid)

        try:
            if dq.one():
                return
        except NoResultFound:
            meta.bind = src.bind

            # src_table = self._src_table_cache.get(tn)
            src_table = Table(tn, meta, autoload=True)
            # if src_table is None:
            #     src_table = Table(tn, meta, autoload=True)
            #     self._src_table_cache[tn] = src_table
            # else:
            #     print 'using cache2 {}'.format(tn)
            nrec = quick_mapper(src_table)
            columns = src_table.columns.keys()

            if verbose:
                msg = 'Transferring records {}'.format(tn)
                if verbose == 1:
                    cols = wrap(columns)
                    msg = '{} {}'.format(msg, 'Columns={}'.format(tn, cols))

                self.debug(msg)

            q = src.query(src_table)
            q = q.filter(getattr(dtable.c, primary_key) == pid)
            try:

                record = q.one()
                # data = dict([(str(column), getattr(record, column)) for column in columns])
                data = {str(column): getattr(record, column) for column in columns}
                dest.merge(nrec(**data))
            except NoResultFound:
                pass

# if __name__=='__main__':
# o=OfflineBridge()
#     o.init('/Users/ross/Sandbox/data.db')
# ============= EOF =============================================

