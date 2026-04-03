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

from __future__ import absolute_import
from __future__ import print_function

from collections import deque
from typing import Dict as TypingDict
from typing import Iterable, List, Optional, Set, Tuple

from traits.api import Any, Bool, Dict, HasTraits

from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser, get_volume
from pychron.extraction_line.canvas.state import (
    NetworkRegionState,
    NetworkSnapshot,
    NetworkValveState,
)
from pychron.extraction_line.graph.nodes import (
    ColdFingerNode,
    Edge,
    GaugeNode,
    GetterNode,
    LaserNode,
    PipetteNode,
    PumpNode,
    RootNode,
    SpectrometerNode,
    TankNode,
    ValveNode,
)


def split_graph(node: ValveNode) -> Tuple:
    """
    Backward-compatible helper for callers that still use legacy split behavior.
    """
    if len(node.edges) == 2:
        edge_a, edge_b = node.edges
        neighbors_a = edge_a.get_nodes(node)
        neighbors_b = edge_b.get_nodes(node)
        try:
            node_a, node_b = neighbors_a[0], neighbors_b[0]
        except IndexError:
            return tuple()

        if not isinstance(node_a, ValveNode):
            return node_b, node_a
        return node_a, node_b

    if node.edges:
        return (node.edges[0].get_nodes(node)[0],)
    return tuple()


class ExtractionLineGraph(HasTraits):
    nodes = Dict
    suppress_changes = False
    inherit_state = Bool

    _cp = None
    _yd = None
    _edges: List[Edge]
    _last_snapshot = Any

    def __init__(self, *args, **kw) -> None:
        super(ExtractionLineGraph, self).__init__(*args, **kw)
        self._edges = []
        self._last_snapshot = None

    def _findname(self, elem, tag: str) -> str:
        if self._cp:
            value = elem.find(tag).text
        else:
            value = elem.get(tag)
            if isinstance(value, dict):
                value = str(value["name"])
        return value.strip()

    def _get_volume(self, elem, tag: str = "volume", default: float = 0) -> float:
        if self._cp:
            return get_volume(elem, tag, default)
        return elem.get(tag, default)

    def _get_text(self, elem) -> str:
        if self._cp:
            text = elem.text
        else:
            text = str(elem.get("name", ""))
        return text.strip()

    def _get_elements(self, key: str) -> list:
        if self._cp:
            return self._cp.get_elements(key)
        return self._yd.get(key, [])

    def _add_edge(
        self, nodes: TypingDict[str, RootNode], edge: Edge, node_names: Iterable[str]
    ) -> None:
        connected = []
        for name in node_names:
            if name in nodes:
                node = nodes[name]
                edge.nodes.append(node)
                node.add_edge(edge)
                connected.append(name)
        delimiter = "-" if len(connected) > 2 else "_"
        edge.name = delimiter.join(connected)
        self._edges.append(edge)

    def load(self, path: str) -> None:
        self._cp = None
        self._yd = None
        self._edges = []

        if path.endswith(".yaml") or path.endswith(".yml"):
            from pychron.core.yaml import yload

            self._yd = yload(path)
        else:
            self._cp = CanvasParser(path)
            if self._cp.get_root() is None:
                self.nodes = {}
                return

        nodes: TypingDict[str, RootNode] = {}
        for tag, klass in (
            ("stage", RootNode),
            ("circle_stage", RootNode),
            ("spectrometer", SpectrometerNode),
            ("valve", ValveNode),
            ("rough_valve", ValveNode),
            ("manual_valve", ValveNode),
            ("turbo", PumpNode),
            ("ionpump", PumpNode),
            ("laser", LaserNode),
            ("circle_laser", LaserNode),
            ("tank", TankNode),
            ("pipette", PipetteNode),
            ("gauge", GaugeNode),
            ("getter", GetterNode),
            ("coldfinger", ColdFingerNode),
        ):
            for element in self._get_elements(tag):
                name = self._get_text(element)
                if not name:
                    continue
                if tag in ("valve", "rough_valve", "manual_valve"):
                    open_volume = self._get_volume(element, tag="open_volume", default=10)
                    closed_volume = self._get_volume(
                        element, tag="closed_volume", default=5
                    )
                    volume = (open_volume, closed_volume)
                else:
                    volume = self._get_volume(element)

                nodes[name] = klass(name=name, volume=volume)

        for tag in ("connection", "elbow", "vconnection", "hconnection", "rconnection"):
            for element in self._get_elements(tag):
                start = self._findname(element, "start")
                end = self._findname(element, "end")
                edge = Edge(volume=self._get_volume(element))
                self._add_edge(nodes, edge, (start, end))

        for tag in ("tee_connection", "fork_connection"):
            for element in self._get_elements(tag):
                left = self._findname(element, "left")
                right = self._findname(element, "right")
                mid = self._findname(element, "mid")
                edge = Edge(volume=self._get_volume(element))
                self._add_edge(nodes, edge, (left, mid, right))

        self.nodes = nodes
        self._last_snapshot = self.compute_state()

    def set_default_states(self, canvas) -> None:
        for name, node in self.nodes.items():
            if isinstance(node, ValveNode):
                self.set_valve_state(name, False)
        self.set_canvas_states(canvas, "")

    def set_valve_state(self, name: str, state, *args, **kw) -> None:
        if name in self.nodes:
            node = self.nodes[name]
            if isinstance(node, ValveNode):
                node.state = "open" if state else "closed"
        self._last_snapshot = None

    def _iter_open_region(
        self, start: RootNode, visited: Set[str]
    ) -> Tuple[List[RootNode], List[Edge], Set[str]]:
        nodes: List[RootNode] = []
        edges: Set[Edge] = set()
        boundaries: Set[str] = set()
        queue = deque([start])

        while queue:
            node = queue.popleft()
            if node is None or node.name in visited or node.state == "closed":
                continue

            visited.add(node.name)
            nodes.append(node)
            for edge in node.edges:
                saw_open_neighbor = False
                for neighbor in edge.get_nodes(node):
                    if neighbor is None:
                        continue
                    if neighbor.state == "closed":
                        if isinstance(neighbor, ValveNode):
                            boundaries.add(neighbor.name)
                        continue
                    saw_open_neighbor = True
                    if neighbor.name not in visited:
                        queue.append(neighbor)

                if saw_open_neighbor:
                    edges.add(edge)

        return nodes, list(edges), boundaries

    def _make_region_id(self, nodes: Iterable[RootNode]) -> str:
        names = sorted(node.name for node in nodes)
        return "region:{}".format("|".join(names))

    def _source_rank(self, node: RootNode) -> Tuple[int, int, str, str]:
        tag_priority = {
            "pump": 0,
            "pipette": 1,
            "laser": 2,
            "tank": 3,
            "spectrometer": 4,
            "coldfinger": 5,
            "getter": 6,
            "gauge": 7,
        }
        tag = getattr(node, "tag", "")
        return (
            -getattr(node, "precedence", 0),
            tag_priority.get(tag, 99),
            tag,
            node.name,
        )

    def _dominant_source(
        self, nodes: Iterable[RootNode]
    ) -> Tuple[str, str, Optional[RootNode]]:
        candidates = [
            node for node in nodes if getattr(node, "precedence", 0) and hasattr(node, "tag")
        ]
        if not candidates:
            return "", "", None

        selected = sorted(candidates, key=self._source_rank)[0]
        return getattr(selected, "tag", ""), selected.name, selected

    def _component_volume(self, nodes: Iterable[RootNode], edges: Iterable[Edge]) -> float:
        return sum(node.volume for node in nodes) + sum(edge.volume for edge in edges)

    def _adjacent_regions(
        self, valve: ValveNode, node_to_region: TypingDict[str, str]
    ) -> List[str]:
        region_ids: Set[str] = set()
        for edge in valve.edges:
            for neighbor in edge.get_nodes(valve):
                if neighbor is None or neighbor.state == "closed":
                    continue
                region_id = node_to_region.get(neighbor.name)
                if region_id:
                    region_ids.add(region_id)
        return sorted(region_ids)

    def compute_state(self) -> NetworkSnapshot:
        if self._last_snapshot is not None:
            return self._last_snapshot

        regions = {}
        valves = {}
        node_states = {}
        edge_states = {}
        node_to_region = {}
        blocked_boundaries: Set[str] = set()
        visited: Set[str] = set()
        for node_name in sorted(self.nodes):
            node = self.nodes[node_name]
            if node.state == "closed" or node.name in visited:
                continue

            region_nodes, region_edges, boundaries = self._iter_open_region(node, visited)
            if not region_nodes:
                continue

            region_id = self._make_region_id(region_nodes)
            dominant_source, dominant_name, dominant_node = self._dominant_source(
                region_nodes
            )
            region = NetworkRegionState(
                identifier=region_id,
                node_names=sorted(node.name for node in region_nodes),
                edge_names=sorted(edge.name for edge in region_edges),
                boundary_valves=sorted(boundaries),
                dominant_source=dominant_source,
                dominant_source_node=dominant_name,
                volume=self._component_volume(region_nodes, region_edges),
            )
            regions[region_id] = region
            blocked_boundaries.update(boundaries)

            for region_node in region_nodes:
                node_to_region[region_node.name] = region_id
                node_states[region_node.name] = {
                    "is_active": True,
                    "region_id": region_id,
                    "dominant_source": dominant_source,
                    "dominant_source_node": dominant_name,
                }

            color_source = dominant_name if dominant_node is not None else ""
            for region_edge in region_edges:
                edge_states[region_edge.name] = {
                    "is_active": True,
                    "region_id": region_id,
                    "dominant_source": dominant_source,
                    "dominant_source_node": color_source,
                }

        for node in self.nodes.values():
            if not isinstance(node, ValveNode):
                continue

            if node.state == "closed":
                adjacent_regions = self._adjacent_regions(node, node_to_region)
                side_volumes = [regions[rid].volume for rid in adjacent_regions if rid in regions]
                max_side_volume = max(side_volumes) if side_volumes else 0
                dominant_source = ""
                dominant_source_node = ""
                if adjacent_regions:
                    dominant_region = max(adjacent_regions, key=lambda rid: regions[rid].volume)
                    dominant_source = regions[dominant_region].dominant_source
                    dominant_source_node = regions[dominant_region].dominant_source_node

                valves[node.name] = NetworkValveState(
                    name=node.name,
                    region_id="",
                    dominant_source=dominant_source,
                    dominant_source_node=dominant_source_node,
                    region_volume=max_side_volume,
                    valve_volume=node.volume,
                    side_volumes=side_volumes,
                    blocked_by_closed=bool(adjacent_regions),
                    blocked_boundaries=list(adjacent_regions),
                )
                node_states[node.name] = {
                    "is_active": False,
                    "region_id": "",
                    "dominant_source": dominant_source,
                    "dominant_source_node": dominant_source_node,
                }
            else:
                region_id = node_to_region.get(node.name, "")
                region = regions.get(region_id)
                dominant_source = region.dominant_source if region else ""
                dominant_source_node = region.dominant_source_node if region else ""
                blocked_for_region = region.boundary_valves if region else []

                valves[node.name] = NetworkValveState(
                    name=node.name,
                    region_id=region_id,
                    dominant_source=dominant_source,
                    dominant_source_node=dominant_source_node,
                    region_volume=region.volume if region else 0,
                    valve_volume=node.volume,
                    side_volumes=[],
                    blocked_by_closed=bool(blocked_for_region),
                    blocked_boundaries=list(blocked_for_region),
                )

        snapshot = NetworkSnapshot(
            regions=regions,
            valves=valves,
            node_states=node_states,
            edge_states=edge_states,
            node_to_region=node_to_region,
            region_count=len(regions),
            blocked_boundaries=sorted(blocked_boundaries),
        )
        self._last_snapshot = snapshot
        return snapshot

    def calculate_volumes(self, node) -> List[Tuple[str, float]]:
        if isinstance(node, str):
            node_obj = self.nodes.get(node)
        else:
            node_obj = node
        if node_obj is None:
            return [(0, 0)]

        if not isinstance(node_obj, ValveNode):
            snapshot = self.compute_state()
            region_id = snapshot.node_to_region.get(node_obj.name, "")
            region = snapshot.regions.get(region_id)
            return [(region_id or node_obj.name, region.volume if region else 0)]

        snapshot = self.compute_state()
        valve_state = snapshot.valves.get(node_obj.name)
        if valve_state is None:
            return [(node_obj.name, 0)]

        if valve_state.side_volumes:
            labels = valve_state.blocked_boundaries
            return list(zip(labels, valve_state.side_volumes))
        label = valve_state.region_id or node_obj.name
        return [(label, valve_state.region_volume)]

    def set_canvas_states(self, canvas, name: str) -> None:
        if self.suppress_changes:
            return
        snapshot = self.compute_state()
        if hasattr(canvas, "apply_network_snapshot"):
            canvas.apply_network_snapshot(snapshot)
        elif hasattr(canvas, "canvas2D") and hasattr(canvas.canvas2D, "apply_network_snapshot"):
            canvas.canvas2D.apply_network_snapshot(snapshot)

    def __getitem__(self, key):
        if not isinstance(key, str):
            key = key.name
        if key in self.nodes:
            return self.nodes[key]
        return None


if __name__ == "__main__":
    graph = ExtractionLineGraph()
    graph.load("/Users/ross/Pychrondata_dev/setupfiles/canvas2D/canvas.xml")
    graph.set_valve_state("C", True)
    graph.set_valve_state("D", True)
    graph.set_valve_state("D", False)
    print(graph.calculate_volumes("D"))

# ============= EOF =============================================
