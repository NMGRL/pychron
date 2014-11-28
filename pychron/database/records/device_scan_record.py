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

#============= enthought library imports =======================
from traitsui.api import View

from pychron.database.records.sqlite_record import SQLiteRecord

#============= standard library imports ========================
#============= local library imports  ==========================
#    def load_graph(self, graph=None, xoffset=0):
#
#        if graph is None:
#            graph = self._graph_factory(klass=TimeSeriesGraph)
#            graph.new_plot(xtitle='Time',
#                       ytitle='Value',
#                       padding=[40, 10, 10, 40]
#                       )
#
#        xi, yi = self._get_data()
#        if xi is not None:
#            graph.new_series(array(xi) + xoffset, yi)
#
#        self.graph = graph
#
#        return max(xi)
#
#    def _get_data(self):
#        dm = self._data_manager_factory()
#        dm.open_data(self._get_path())
#        xi = None
#        yi = None
#        if isinstance(dm, H5DataManager):
#            s1 = dm.get_table('scan1', 'scans')
#            if s1 is not None:
#                xi, yi = zip(*[(r['time'], r['value']) for r in s1.iterrows()])
#            else:
#                self._loadable = False
#        else:
#            da = dm.read_data()
#            if da is not None:
#                xi, yi = da
#        return xi, yi

class DeviceScanRecord(SQLiteRecord):

    def load_graph(self):
        pass

    def traits_view(self):
        v = View()
        return v

# ============= EOF =============================================
