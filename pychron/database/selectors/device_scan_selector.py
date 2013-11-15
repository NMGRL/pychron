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
from traits.api import Bool
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.core.database_selector import DatabaseSelector
from pychron.database.orms.hardware_orm import ScanTable
from pychron.database.core.query import compile_query, DeviceScanQuery
from pychron.database.records.device_scan_record import DeviceScanRecord

class DeviceScanSelector(DatabaseSelector):
    record_klass = DeviceScanRecord
    query_klass = DeviceScanQuery
    title = 'Device Scans'

    def _get_selector_records(self, queries=None, limit=None, **kw):
        sess = self.db.get_session()
        q = sess.query(ScanTable)
        lookup = dict()
        q = self._assemble_query(q, queries, lookup)
        records = q.all()

        return records, compile_query(q)


#============= EOF =============================================
