# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Dict, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.extraction_line.graph.nodes import ValveNode, RootNode, \
    PumpNode, Edge, SpectrometerNode, LaserNode, TankNode, PipetteNode, \
    GaugeNode, GetterNode

from pychron.canvas.canvas2D.scene.primitives.valves import Valve

from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser, get_volume
from pychron.extraction_line.graph.traverse import bft


def split_graph(n):
    """
        valves only have binary connections
        so can only split in half
    """

    if len(n.edges) == 2:
        e1, e2 = n.edges

        n1, n2 = e1.get_nodes(n), e2.get_nodes(n)
        n1, n2 = n1[0], n2[0]
        # ensure first node is a Valve node otherwise states not set correctly
        #see issue #335
        if not isinstance(n1, ValveNode):
            return n2, n1
        else:
            return n1, n2
    else:
        if n.edges:
            return n.edges[0].get_nodes(n)[0],
        else:
            return []


class ExtractionLineGraph(HasTraits):
    nodes = Dict
    suppress_changes = False
    inherit_state = Bool

    def load(self, p):

        cp = CanvasParser(p)
        if cp.get_root() is None:
            return

        nodes = dict()

        # =======================================================================
        # load nodes
        # =======================================================================
        # load roots
        for t, klass in (('stage', RootNode),
                         ('spectrometer', SpectrometerNode),
                         ('valve', ValveNode),
                         ('rough_valve', ValveNode),
                         ('turbo', PumpNode),
                         ('ionpump', PumpNode),
                         ('laser', LaserNode),
                         ('tank', TankNode),
                         ('pipette', PipetteNode),
                         ('gauge', GaugeNode),
                         ('getter', GetterNode)):
            for si in cp.get_elements(t):
                n = si.text.strip()
                if t in ('valve', 'rough_valve'):
                    o_vol = get_volume(si, tag='open_volume', default=10)
                    c_vol = get_volume(si, tag='closed_volume', default=5)
                    vol = (o_vol, c_vol)
                else:
                    vol = get_volume(si)

                node = klass(name=n, volume=vol)
                nodes[n] = node

        # =======================================================================
        # load edges
        # =======================================================================
        for ei in cp.get_elements('connection'):
            sa = ei.find('start')
            ea = ei.find('end')
            vol = get_volume(ei)
            edge = Edge(volume=vol)
            s_name = ''
            if sa.text in nodes:
                s_name = sa.text
                sa = nodes[s_name]
                edge.nodes.append(sa)
                sa.add_edge(edge)

            e_name = ''
            if ea.text in nodes:
                e_name = ea.text
                ea = nodes[e_name]
                # edge.b_node = ea
                edge.nodes.append(ea)
                ea.add_edge(edge)

            edge.name = '{}_{}'.format(s_name, e_name)

        for c in ('tee_connection', 'fork_connection'):
            for conn in cp.get_elements(c):
                left = conn.find('left')
                right = conn.find('right')
                mid = conn.find('mid')

                edge = Edge(vol=get_volume(conn))
                lt = left.text.strip()
                rt = right.text.strip()
                mt = mid.text.strip()

                ns = []
                for x in (lt, mt, rt):
                    if x in nodes:
                        ln = nodes[x]
                        edge.nodes.append(ln)
                        ln.add_edge(edge)
                        ns.append(x)

                edge.name = '-'.join(ns)

        self.nodes = nodes

    def set_default_states(self, canvas):
        for ni in self.nodes:
            if isinstance(ni, ValveNode):
                self.set_valve_state(ni, False)
            self.set_canvas_states(canvas, ni)

    def set_valve_state(self, name, state, *args, **kw):
        if name in self.nodes:
            v_node = self.nodes[name]
            v_node.state = 'open' if state else 'closed'

    def set_canvas_states(self, canvas, name):
        if not self.suppress_changes:
            if hasattr(canvas, 'scene'):
                scene = canvas.scene
            else:
                scene = canvas.canvas2D.scene
            if name in self.nodes:
                s_node = self.nodes[name]

                # new algorithm
                # if valve closed
                #    split tree and fill each sub tree
                # else:
                #    for each edge of the start node
                #        breath search for the max state
                #
                #    find max max_state
                #    fill nodes with max_state
                #        using a depth traverse
                #
                # new variant
                # recursively split tree if node is closed

                self._set_state(s_node, scene)
                self._clear_visited()

    def _set_state(self, n, scene=None):

        if n:
            if n.state == 'closed' and not n.visited:
                n.visited = True
                # print 'splitting on {}'.format(n.name)
                #print ','.join([x.name for x in split_graph(n)])
                for ni in split_graph(n):
                    self._set_state(ni, scene)
            else:
                state, term = self._find_max_state(n)
                # print state, term, n.__class__.__name__, n.name
                self.fill(scene, n, state, term)
                self._clear_fvisited()

    def calculate_volumes(self, node):
        if isinstance(node, str):
            if node not in self.nodes:
                return [(0, 0), ]

            node = self.nodes[node]

        if node.state == 'closed':
            nodes = split_graph(node)
        else:
            nodes = (node, )

        vs = [(ni.name, self._calculate_volume(ni)) for ni in nodes]
        self._clear_fvisited()
        return vs

    def _calculate_volume(self, node, k=0):
        """
            use a Depth-first Traverse
            accumulate volume
        """
        debug = False
        vol = node.volume
        node.f_visited = True
        if debug:
            print '=' * (k + 1), node.name, node.volume, vol

        for i, ei in enumerate(node.edges):
            # ns = ei.get_nodes(node)
            for n in ei.get_nodes(node):
                if n is None:
                    continue

                vol += ei.volume
                if debug:
                    print '-' * (k + i + 1), ei.name, ei.volume, vol

                if not n.f_visited:
                    n.f_visited = True
                    if n.state == 'closed':
                        vol += n.volume
                        if debug:
                            print 'e' * (k + i + 1), n.name, n.volume, vol

                    else:
                        v = self._calculate_volume(n, k=k + 1)
                        vol += v
                        if debug:
                            print 'n' * (k + i + 1), n.name, v, vol

        return vol

    def _find_max_state(self, node):
        """
            use a Breadth-First Traverse
            acumulate the max state at each node
        """
        m_state, term = False, ''

        for ni in bft(self, node):

            if isinstance(ni, PumpNode):
                return 'pump', ni.name

            if isinstance(ni, LaserNode):
                m_state, term = 'laser', ni.name
            elif isinstance(ni, PipetteNode):
                m_state, term = 'pipette', ni.name

            if m_state not in ('laser', 'pipette'):
                if isinstance(ni, SpectrometerNode):
                    m_state, term = 'spectrometer', ni.name
                elif isinstance(ni, TankNode):
                    m_state, term = 'tank', ni.name
                elif isinstance(ni, GetterNode):
                    m_state, term = 'getter', ni.name
        else:

            return m_state, term

    def fill(self, scene, root, state, term):
        self._set_item_state(scene, root.name, state, term)
        for ei in root.edges:
            # n = ei.get_nodes(root)
            for n in ei.get_nodes(root):
                if n is None:
                    continue
                self._set_item_state(scene, ei.name, state, term)

                if n.state != 'closed' and not n.f_visited:
                    n.f_visited = True
                    self.fill(scene, n, state, term)

    def _set_item_state(self, scene, name, state, term, color=None):
        if not isinstance(name, str):
            raise ValueError('name needs to be a str. provided={}'.format(name))

        obj = scene.get_item(name)
        if obj is None or obj.type_tag in ('turbo', 'tank', 'ionpump'):
            return

        if not color and state:
            color = scene.get_item(term).default_color

        if isinstance(obj, Valve):

            # set the color of the valve to
            # the max state if the valve is open
            if self.inherit_state:
                if obj.state != 'closed':
                    if state:
                        obj.active_color = color
                    else:
                        obj.active_color = obj.oactive_color

            return

        if state:
            obj.active_color = color
            obj.state = True
        else:
            obj.state = False

    def _clear_visited(self):
        for ni in self.nodes.itervalues():
            ni.visited = False

    def _clear_fvisited(self):
        for ni in self.nodes.itervalues():
            ni.f_visited = False

    def __getitem__(self, key):
        if not isinstance(key, str):
            key = key.name

        if key in self.nodes:
            return self.nodes[key]

            # def _get_node(self, name):
            #     return bfs(self, self.root, name)


if __name__ == '__main__':
    elg = ExtractionLineGraph()
    elg.load('/Users/ross/Pychrondata_dev/setupfiles/canvas2D/canvas.xml')
    elg.set_valve_state('C', True)
    elg.set_valve_state('D', True)

    elg.set_valve_state('D', False)
    elg._set_state(elg.nodes['D'])
    # elg.set_canvas_states('D')
    # print elg.calculate_volumes('Obama')
    #print elg.calculate_volumes('Bone')
    #state, root = elg.set_valve_state('H', True)
    #state, root = elg.set_valve_state('H', False)

    #print '-------------------------------'
    #print state, root

# ============= EOF =============================================
