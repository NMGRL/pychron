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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.orms.bakeout_orm import BakeoutTable
from pychron.database.core.database_selector import DatabaseSelector
from pychron.database.core.query import BakeoutQuery
from pychron.database.records.bakeout_record import BakeoutRecord
from traitsui.tabular_adapter import TabularAdapter

#

# class BakeoutTabularAdapter(TabularAdapter):
#    columns = [('ID', 'record_id'),
#               ('Timestamp', 'timestamp')
#               ]

class BakeoutDBSelector(DatabaseSelector):

    query_table = BakeoutTable
    record_klass = BakeoutRecord
    record_view_klass = BakeoutRecord
    query_klass = BakeoutQuery
#    tabular_adapter = BakeoutTabularAdapter
    lookup = {'Run Date':([], BakeoutTable.timestamp), }

    dclick_recall_enabled = True
#    def _record_factory(self, idn):
#        return idn

    def _get_selector_records(self, queries=None, limit=None, **kw):
        sess = self.db.get_session()
        q = sess.query(self.query_table)
        return self._get_records(q, queries, limit)

#============= EOF =============================================

