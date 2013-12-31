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
# from pychron.core.ui import set_toolkit
# set_toolkit('qt4')
#============= enthought library imports =======================
import os
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base

#============= standard library imports ========================
#============= local library imports  ==========================
from sqlalchemy.orm.exc import NoResultFound
from pychron.core.helpers.logger_setup import wrap
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.orms.isotope.util import Base
from pychron.paths import paths



def quick_mapper(table):
    Base = declarative_base()

    class GenericMapper(Base):
        __table__ = table

    return GenericMapper


class OfflineBridge(IsotopeAdapter):
    """
        use to gather data from mysql and save to sqlite
    """
    kind = 'sqlite'

    def init(self, p=None):

        #create a default db
        if p is None:
            p = os.path.join(paths.hidden_dir, 'data.db')

        self.debug('init database {}'.format(p))
        self.path = p
        self.connect()
        if not os.path.isfile(p):
            self.debug('init creating all tables')
            metadata=Base.metadata
            self.create_all(metadata)

    def add_analyses(self, db, ans):
        self.debug('adding analyses')
        self.debug('source={}'.format(db.url))
        self.debug('dest={}'.format(self.path))
        self.connect()

        src = db.sess
        with self.session_ctx() as dest:
            for ai in ans:
                if not self.get_analysis_uuid(ai.uuid):
                    ln=ai.labnumber
                    if ln:
                        self.debug('copying analysis {}'.format(ai.record_id))

                        #get the source objects
                        ai=db.get_analysis_uuid(ai.uuid)
                        ln=db.get_labnumber(ln)

                        # self._copy_table(dest, src, ai.lab_id, 'gen_labtable', gen_LabTable)
                        # self._copy_table(dest, src, ln.sample_id, 'gen_sampletable', gen_SampleTable)
                        #
                        # sample=ln.sample
                        # if sample:
                        #     self._copy_table(dest, src, sample.project_id, 'gen_projecttable', gen_ProjectTable)
                        #     self._copy_table(dest, src, sample.material_id, 'gen_materialtable', gen_MaterialTable)

                        self._copy_table(dest, src, ai.lab_id, 'gen_labtable')
                        self._copy_table(dest, src, ln.sample_id, 'gen_sampletable')

                        sample = ln.sample
                        if sample:
                            self._copy_table(dest, src, sample.project_id, 'gen_projecttable')
                            self._copy_table(dest, src, sample.material_id, 'gen_materialtable')

                        self._copy_table(dest, src, ln.irradiation_id, 'irrad_positiontable')
                        self._copy_table(dest, src, ln.irradiation_position.level_id, 'irrad_leveltable')
                        self._copy_table(dest, src, ln.irradiation_position.level.irradiation_id, 'irrad_irradiationtable')

                        self._copy_table(dest, src, ai.id, 'meas_analysistable')
                        self._copy_table(dest, src, ai.measurement_id, 'meas_measurementtable')
                        self._copy_table(dest, src, ai.extraction_id, 'meas_extractiontable')
                        dest.commit()

    def _copy_table(self, dest, src, pid, tn, verbose=True):
        meta=Base.metadata
        meta.bind=dest.bind
        dtable = Table(tn, meta, autoload=True)
        dq=dest.query(dtable)
        dq=dq.filter(dtable.c.id==pid)

        try:
            if dq.one():
                return
        except NoResultFound:
            # dq = dest.query(dtable)
            # print dq.all()
            meta.bind = src.bind

            table = Table(tn, meta, autoload=True)
            nrec = quick_mapper(table)
            columns = table.columns.keys()

            if verbose:
                msg='Transferring records {}'.format(tn)
                if verbose==1:
                    cols=wrap(columns)
                    msg='{} {}'.format(msg, 'Columns={}'.format(tn, cols))

                self.debug(msg)

                q=src.query(table)
                q=q.filter(table.c.id==pid)
            try:

                record=q.one()
                data = dict([(str(column), getattr(record, column)) for column in columns])
                dest.merge(nrec(**data))
            except NoResultFound:
                pass

# if __name__=='__main__':
#     o=OfflineBridge()
#     o.init('/Users/ross/Sandbox/data.db')
#============= EOF =============================================

