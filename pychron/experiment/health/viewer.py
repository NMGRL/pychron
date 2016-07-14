# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import HasTraits, Instance
from traitsui.api import View, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.graph.stacked_graph import StackedGraph
from pychron.paths import paths


class AnalysisHealthViewer(HasTraits):
    graph = Instance(StackedGraph, ())
    def load(self):
        series = self._load_series()

        self._add_plot()
        self._add_plot()

    def _add_plot(self):
        g = self.graph
        g.new_plot()
        g.new_series([1,2,3,4,5], [1,23,1231,1,43])


    def _load_series(self):
        series = None
        p = os.path.join(paths.hidden_dir, 'health_series.yaml')
        if os.path.isfile(p):
            with open(p,'r') as rfile:
                series = yaml.load(rfile)
        return series

    def traits_view(self):
        v=View(UItem('graph', style='custom'))
        return v


if __name__ =='__main__':
    # make test data
    for i in range(10):
        pass

    ahv = AnalysisHealthViewer()
    ahv.load()
    ahv.configure_traits()
# ============= EOF =============================================



