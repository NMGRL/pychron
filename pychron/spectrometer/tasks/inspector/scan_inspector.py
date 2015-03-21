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
import os

from numpy import array
from traits.api import HasTraits, Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import fileiter
from pychron.graph.graph import Graph
from pychron.graph.time_series_graph import TimeSeriesStackedGraph
from pychron.paths import paths


class ScanInspector(HasTraits):
    graph = Instance(Graph)

    def activated(self):
        p = os.path.join(paths.spectrometer_scans_dir, 'scan-005.txt')
        g = self.graph
        with open(p, 'r') as fp:
            fi = fileiter(fp, strip=True)

            fi.next().split(',')
            plot = g.new_plot(padding=[60, 5, 5, 50])

            g.set_y_title('Intensity (fA)')

            data = [line.split(',') for line in fi]
            data = array(data, dtype=float).T
            xs = data[0]
            for ys in data[1:]:
                g.new_series(x=xs, y=ys)

            plot.value_scale = 'log'

    def _graph_default(self):
        g = TimeSeriesStackedGraph()
        # g.new_plot()
        return g

# ============= EOF =============================================



