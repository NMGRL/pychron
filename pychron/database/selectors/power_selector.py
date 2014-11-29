# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Float
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.database.core.database_selector import DatabaseSelector
from pychron.database.orms.power_orm import PowerTable
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.database.core.base_db_result import RIDDBResult
from pychron.database.core.query import PowerRecordQuery


class PowerResult(RIDDBResult):
    title_str = 'PowerRecord'
    request_power = Float

    def load_graph(self, *args, **kw):
        g = self._graph_factory()

        dm = self.data_manager
        internal = dm.get_table('internal', 'Power')
        brightness = dm.get_table('brightness', 'Power')
        g.new_plot(xtitle='Time (s)',
                   ytitle='Internal/Brightness Power Meter',
                   padding=[50, 10, 10, 40])
        if internal is not None:
            xi, yi = zip(*[(r['time'], r['value']) for r in internal.iterrows()])
            g.new_series(xi, yi)
        if brightness is not None:
            xb, yb = zip(*[(r['time'], r['value']) for r in brightness.iterrows()])
            g.new_series(xb, yb)

        self.graph = g

    def _load_hook(self, dbr):
        data = os.path.join(self.directory, self.filename)
        dm = H5DataManager()
        if os.path.isfile(data):
            dm.open_data(data)

            tab = dm.get_table('internal', 'Power')
            if tab is not None:
                if hasattr(tab.attrs, 'request_power'):
                    self.summary = 'request power ={}'.format(tab.attrs.request_power)
            self.runid = str(dbr.rid)

        self.data_manager = dm

class PowerSelector(DatabaseSelector):
#    parameter = String('PowerTable.rundate')
    query_table = PowerTable
    query_klass = PowerRecordQuery
    title = 'Power Recording'
#    record_klass = PowerResult
#    tabular_adapter = RIDResultsAdapter

    def _get_selector_records(self, **kw):
        return self._db.get_power_records(**kw)


# ============= EOF =============================================
