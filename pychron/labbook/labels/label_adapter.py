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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import SQLiteDatabaseAdapter
from pychron.labbook.labels.orm import LabelTable, PathTable


class LabelAdapter(SQLiteDatabaseAdapter):
    kind = 'sqlite'

    def _build_database(self, sess, meta):
        from orm import Base

        Base.metadata.create_all(sess.bind)

    # adders
    def add_label(self, text, color):
        obj = LabelTable(text=text, color=color)
        self._add_item(obj)

    def add_label_association(self, path, label):
        path = self.get_path(path)
        label = self.get_label(label)
        path.labels.append(label)
        self.commit()

    def add_path(self, p):
        obj = PathTable(relpath=p)
        return self._add_item(obj)

    # getters
    def get_labels(self):
        return self._retrieve_items(LabelTable)

    def get_label(self, text):
        return self._retrieve_item(LabelTable, text, key='text')

    def get_path(self, p):
        return self._retrieve_item(PathTable, p, key='relpath')

    #deleters
    def delete_label(self, text):
        self._delete_item(text, 'label')


if __name__ == '__main__':
    db = LabelAdapter(path='/Users/ross/Sandbox/label.db')
    db.build_database()

# ============= EOF =============================================



