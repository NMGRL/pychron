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

#============= enthought library imports =======================
# from traits.api import String, Instance, Enum, on_trait_change, Bool, \
#    Range
# from traitsui.api import Group, VGroup, Item, HGroup, spring
#============= standard library imports ========================
# import os
# import csv
#============= local library imports  ==========================
from pychron.database.core.database_selector import DatabaseSelector
from pychron.database.orms.power_map_orm import PowerMapTable
# from pychron.database.core.base_db_result import DBResult
# from pychron.graph.graph3D import Graph3D
from pychron.database.core.query import PowerMapQuery, compile_query
from pychron.database.records.power_map_record import PowerMapRecord

#
# class PowerMapResult(DBResult):
#    title_str = 'PowerMap'
#    resizable = False
#    graph3D = Instance(Graph3D, ())
#
#    vertical_ex = Range(1, 100)
#    surf = Bool(True)
#    surf_outline = Bool(True)
#
#    contour = Bool(False)
#    contour_outline = Bool(False)
#    levels = Range(4, 20)
#    representation = Enum('surface', 'wireframe', 'points')
#
#    @on_trait_change('surf+, contour+,\
#                        representation, levels,\
#                        vertical_ex\
#                        ')
#
#    def refresh_graph3d(self):
#        self.graph3D.clear()
#
#        self.load_graph()
#
#    def traits_view(self):
#        twod_graph = self._get_graph_item()
#        twod_graph.label = '2D'
#
#        ctrl_grp = Group(
#                         Item('vertical_ex', label='Vertical Ex.'),
#                         HGroup(Item('contour'),
#                                Item('levels'),
#                                spring,
#                                Item('contour_outline', label='Outline')
#                                ),
#                         HGroup(Item('surf'),
#                                Item('representation'),
#                                spring,
#                                Item('surf_outline', label='Outline')
#                                ),
#                         show_border=True, label='Tweak')
#        threed_graph = Group(VGroup(
#                             Item('graph3D', show_label=False,
#                                  style='custom'
#                                  ),
#                             ctrl_grp
#                                ),
#                             label='3D',
#                             )
#        grps = VGroup(
#                      Group(
#                      twod_graph,
#                      threed_graph,
#                      layout='tabbed'
#                      ),
#                      self._get_info_grp())
#
#        return self._view_factory(grps)
#
#    def load_graph(self, *args, **kw):
#        data = os.path.join(self.directory, self.filename)
#        from pychron.lasers.power.power_map_processor import PowerMapProcessor
#        pmp = PowerMapProcessor()
#        if data.endswith('.h5') or data.endswith('.hdf5'):
#            reader = self._data_manager_factory()
#            reader.open_data(data)
#        else:
#            with open(data, 'r') as f:
#                reader = csv.reader(f)
#                # trim off header
#                reader.next()
# #
#        self.graph = pmp.load_graph(reader)
#        self.graph.width = 625
#        self.graph.height = 500
#
#        reader.open_data(data)
#        z, _ = pmp._extract_h5(reader)
#        if self.surf:
#            self.graph3D.plot_data(z, func='surf',
#                                   representation=self.representation,
#                                   warp_scale=self.vertical_ex ,
#                                   outline=self.surf_outline
#                                   )
#        if self.contour:
#            self.graph3D.plot_data(z, func='contour_surf',
#                                   contours=self.levels,
#                                   warp_scale=self.vertical_ex,
#                                   outline=self.contour_outline
#                                   )



class PowerMapSelector(DatabaseSelector):
#    parameter = String('PowerMapTable.rundate')

    query_klass = PowerMapQuery
    record_klass = PowerMapRecord
    query_table = PowerMapTable
    title = 'Power Map'

#    def _record_factory(self, idn):
#        return idn

    def _get_selector_records(self, queries=None, limit=None, **kw):
#        return self.db.get_powermaps(**kw)
        sess = self.db.get_session()
        q = sess.query(PowerMapTable)
        lookup = dict()
        q = self._assemble_query(q, queries, lookup)
        records = q.all()

        return records, compile_query(q)
# ============= EOF =============================================
