# ===============================================================================
# Copyright 2012 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import Integer, DateTime, String, Float
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.orms.local_lab_orm import LabTable
# ============= standard library imports ========================
import os


# ============= local library imports  ==========================

class LocalLabAdapter(DatabaseAdapter):
    kind = 'sqlite'

    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.path):
            sess = self.get_session()
            meta = MetaData()
            bt = Table('LabTable', meta,
                       Column('id', Integer, primary_key=True),
                       Column('labnumber', String(40)),
                       Column('aliquot', Integer),
                       Column('step', String(20)),
                       Column('uuid', String(40)),
                       Column('mass_spectrometer', String(40)),
                       Column('extract_device', String(40)),
                       Column('extract_value', Float),
                       Column('cleanup', Float),
                       Column('duration', Float),

                       Column('collection_path', String(200)),
                       Column('repository_path', String(200)),
                       Column('create_date', DateTime))
            bt.create(sess.bind)

    def add_analysis(self, **kw):
        l = LabTable(**kw)
        self._add_item(l)
        return l

    def get_last_analysis(self):
        with self.session_ctx() as sess:
            q = sess.query(LabTable)
            q = q.order_by(LabTable.create_date.desc())
            q = q.limit(1)
            try:
                return q.one()
            except NoResultFound, e:
                pass

if __name__ == '__main__':
    lb = LocalLabAdapter(name='/Users/ross/Sandbox/foo.db')
    lb.build_database()
# ============= EOF =============================================
