# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, List, Str, Instance, Float, Property

# ============= standard library imports ========================
import weakref
# ============= local library imports  ==========================


def flatten(nested):
#     print nested
    if isinstance(nested, str):
        yield nested
    else:
        try:
            for sublist in nested:
                for element in flatten(sublist):
                    yield element

        except TypeError:
            yield nested


class Edge(HasTraits):
    name = Str
    a_node = Instance('pychron.extraction_line.graph.nodes.Node')
    b_node = Instance('pychron.extraction_line.graph.nodes.Node')
    visited = False
    volume = Float(1)

    def nodes(self):
        return self.a_node, self.b_node

    def get_node(self, n):
        return self.b_node if self.a_node == n else self.a_node


class Node(HasTraits):
    edges = List

    name = Str
    state = Str
    visited = False
    f_visited = False
    volume = Float

    def add_edge(self, n):
        self.edges.append(weakref.ref(n)())

    def __iter__(self):
        for ei in self.edges:
            n = ei.get_node(self)
            yield n


class ValveNode(Node):
    state = 'closed'
    volume = Property
    _closed_volume = Float(5)

    '''
        the additional volume when a valve is open
    '''
    _open_volume = Float(10)

    def _set_volume(self, v):
        o_vol, c_vol = v
        self._open_volume = o_vol
        self._closed_volume = c_vol

    def _get_volume(self):
        v = self._closed_volume
        if self.state != 'closed':
            v += self._open_volume
        return v


class RootNode(Node):
    state = True


class GaugeNode(RootNode):
    pass


class PumpNode(RootNode):
    pass


class SpectrometerNode(RootNode):
    pass


class TankNode(RootNode):
    pass


class PipetteNode(RootNode):
    pass


class LaserNode(RootNode):
    pass


# ============= EOF =============================================
