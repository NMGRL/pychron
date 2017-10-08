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

# ============= standard library imports ========================
import os

from sqlalchemy.orm.exc import NoResultFound
# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.orms.local_lab_orm import LabTable, Base


class LocalLabAdapter(DatabaseAdapter):
    def __init__(self, *args, **kw):
        super(LocalLabAdapter, self).__init__(*args, **kw)
        self.kind = 'sqlite'
        if not self.path:
            self.path = os.path.join(paths.hidden_dir, 'local_lab.db')

    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.path):
            with self.session_ctx() as sess:
                Base.metadata.tables['LabTable'].create(bind=sess.bind)

    def add_analysis(self, **kw):
        l = LabTable(**kw)
        self._add_item(l)
        return l

    def get_last_analysis(self):
        q = self.session.query(LabTable)
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
