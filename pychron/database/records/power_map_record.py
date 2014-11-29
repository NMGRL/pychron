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
from traits.api import Bool, Instance, Enum, Range, on_trait_change, Any
from traitsui.api import HGroup, Group, Item, spring , VGroup

from pychron.database.records.sqlite_record import SQLiteRecord

# ============= standard library imports ========================
# import os
import csv
from pychron.managers.data_managers.h5_data_manager import H5DataManager

from pychron.graph.contour_graph import ContourGraph
# ============= local library imports  ==========================
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

class PowerMapRecord(SQLiteRecord):
    title_str = 'PowerMap'
    resizable = True
#    graph3D = Instance(Graph3D, ())
    graph3D = Any  # Instance(Graph3D, ())
    graph = Instance(ContourGraph)
    vertical_ex = Range(1, 100)
    surf = Bool(True)
    surf_outline = Bool(True)

    contour = Bool(False)
    contour_outline = Bool(False)
    levels = Range(4, 20)
    representation = Enum('surface', 'wireframe', 'points')

    def initialize(self):
        self.load_graph()
        return True

    @on_trait_change('surf+, contour+,\
                        representation, levels,\
                        vertical_ex\
                        ')
    def refresh_graph3d(self):
        self.graph3D.clear()
        self.load_graph()

    def traits_view(self):
        twod_graph = Group(Item('graph',
                                show_label=False,
                                style='custom',
#                                height=1.0
                                ),
                  label='2D'
                  )

#        twod_graph = self._get_graph_item()
#        twod_graph.label = '2D'

        ctrl_grp = Group(
                         Item('vertical_ex', label='Vertical Ex.'),
                         HGroup(Item('contour'),
                                Item('levels'),
                                spring,
                                Item('contour_outline', label='Outline')
                                ),
                         HGroup(Item('surf'),
                                Item('representation'),
                                spring,
                                Item('surf_outline', label='Outline')
                                ),
                         show_border=True, label='Tweak')
        threed_graph = Group(VGroup(
                             Item('graph3D', show_label=False,
                                  style='custom'
                                  ),
                             ctrl_grp
                                ),
                             label='3D',
                             )
#        grps = VGroup(
        grps = Group(
                      twod_graph,
                      threed_graph,
                      layout='tabbed'
                      )
#                      self._get_info_grp()
#                      )
#        grps = twod_graph
        return self._view_factory(grps)

    def load_graph(self):
        path = self.path
#        path = os.path.join(self.root, self.filename)
        from pychron.lasers.power.power_map_processor import PowerMapProcessor
        pmp = PowerMapProcessor()
        if path.endswith('.h5') or path.endswith('.hdf5'):
            reader = H5DataManager()
#            reader = self._data_manager_factory()
            reader.open_data(path)
        else:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                # trim off header
                reader.next()
#
        self.graph = pmp.load_graph(reader)
        self.graph.width = 625
        self.graph.height = 500

        reader.open_data(path)
        z, _ = pmp._extract_h5(reader)
        if self.surf:
            self.graph3D.plot_data(z, func='surf',
                                   representation=self.representation,
                                   warp_scale=self.vertical_ex ,
                                   outline=self.surf_outline
                                   )
        if self.contour:
            self.graph3D.plot_data(z, func='contour_surf',
                                   contours=self.levels,
                                   warp_scale=self.vertical_ex,
                                   outline=self.contour_outline
                                   )

    def _graph3D_default(self):
        from pychron.graph.graph3D import Graph3D
        return Graph3D()
#    def traits_view(self):
#        v = View()
#        return v

# ============= EOF =============================================
