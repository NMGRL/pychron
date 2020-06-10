# ===============================================================================
# Copyright 2019 ross
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
from numpy import array, column_stack
from sklearn.cluster import KMeans, AffinityPropagation, MeanShift, estimate_bandwidth, DBSCAN
from sklearn.preprocessing import StandardScaler
from traits.api import List, Instance
from traitsui.api import View, UItem
from uncertainties import nominal_value

from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.graph import Graph


class ClusterEditor(BaseTraitsEditor):
    items = List

    graph = Instance(Graph)

    def set_items(self, items):
        self.items = items

        self.graph = g = Graph()
        p = g.new_plot()
        p.value_range.tight_bounds = False
        p.index_range.tight_bounds = False
        xattr = 'age'
        yattr = 'kca'

        g.set_x_title('Age')
        g.set_y_title('K/Ca')

        cluster_kind = self.plotter_options.cluster_kind

        xs = self._extract_attr(items, xattr)
        ys = self._extract_attr(items, yattr)

        xx = column_stack((xs, ys))
        xx = StandardScaler().fit_transform(xx)
        if cluster_kind == 'kmeans':
            clusterer = KMeans
            kw = {'n_clusters': 2}
        elif cluster_kind == 'meanshift':
            clusterer = MeanShift
            ebw = estimate_bandwidth(xx)
            kw = {'bandwidth': ebw}
        elif cluster_kind == 'dbscan':
            clusterer = DBSCAN
            kw = {}
        else:
            clusterer = AffinityPropagation
            kw = {'preference': -50}

        cs = clusterer(**kw).fit_predict(xx)
        g.new_series(xs, ys, colors=cs, type='cmap_scatter')

    def _extract_attr(self, items, attr):
        return array([nominal_value(ai.get_value(attr)) for ai in items])

    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v


if __name__ == '__main__':
    import random


    class I:
        def __init__(self, scale):
            self._scale = scale

        def get_value(self, item):
            return random.random() + self._scale


    c = ClusterEditor()
    c.set_items([I(1) for i in range(100)] + [I(10) for i in range(100)])
    c.configure_traits()
# ============= EOF =============================================
