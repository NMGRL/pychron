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
import os
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base

#============= standard library imports ========================
#============= local library imports  ==========================
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

    def init(self):
        #create a default db
        p = os.path.join(paths.hidden_dir, 'data.db')
        self.path = p

        if not os.path.isfile(p):
            metadata=Base.metadata
            self.create_all(metadata)

    def add_analyses(self, db, ans):

        self.connect()

        src = db.sess
        with self.session_ctx() as dest:
            for ai in ans:
                self._copy_table(dest, src, ai.lab_id, 'gen_labtable')
                self._copy_table(dest, src, ai.labnumber.sample_id, 'gen_sampletable')
                self._copy_table(dest, src, ai.labnumber.sample.project_id, 'gen_projecttable')
                self._copy_table(dest, src, ai.labnumber.sample.material_id, 'gen_materialtable')

                self._copy_table(dest, src, ai.labnumber.irradiation_id, 'irrad_positiontable')
                self._copy_table(dest, src, ai.labnumber.irradiation_position.level_id, 'irrad_leveltable')
                self._copy_table(dest, src, ai.labnumber.irradiation_position.level.irradiation_id, 'irrad_irradiationtable')

                self._copy_table(dest, src, ai.id, 'meas_analysistable')
                self._copy_table(dest, src, ai.measurement_id, 'meas_measurementtable')
                self._copy_table(dest, src, ai.extraction_id, 'meas_extractiontable')

    def _copy_table(self, dest, src, pid, tn):
        meta = Base.metadata
        table = Table(tn, meta, autoload=True)
        nrec = quick_mapper(table)
        columns = table.columns.keys()
        self.debug('Transferring records Columns={}'.format(','.join(columns)))
        q=src.query(table)
        q=q.filter(table.id==pid)
        for record in q.all():
            data = dict([(str(column), getattr(record, column)) for column in columns])
            dest.merge(nrec(**data))


#============= EOF =============================================

