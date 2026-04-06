import json
import os
import sys
import tempfile
import types
import unittest

if "yaml" not in sys.modules:

    def _yaml_load(stream, Loader=None):
        data = stream.read() if hasattr(stream, "read") else stream
        return json.loads(data)

    def _yaml_dump(obj, default_flow_style=False):
        return json.dumps(obj)

    yaml_stub = types.SimpleNamespace(
        FullLoader=object,
        Loader=object,
        YAMLError=Exception,
        load=_yaml_load,
        dump=_yaml_dump,
        safe_dump=_yaml_dump,
    )
    sys.modules["yaml"] = yaml_stub

from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.canvas.canvas2D.scene.primitives.connections import Connection
from pychron.canvas.canvas2D.scene.primitives.valves import Switch
from pychron.extraction_line.graph.extraction_line_graph import ExtractionLineGraph
from pychron.extraction_line.graph.nodes import (
    Edge,
    LaserNode,
    PipetteNode,
    PumpNode,
    SpectrometerNode,
    TankNode,
    ValveNode,
)


def connect(node_a, node_b, volume=1) -> Edge:
    edge = Edge(name="{}_{}".format(node_a.name, node_b.name), volume=volume)
    edge.nodes = [node_a, node_b]
    node_a.add_edge(edge)
    node_b.add_edge(edge)
    return edge


def make_graph() -> ExtractionLineGraph:
    graph = ExtractionLineGraph()
    pump = PumpNode(name="P", volume=0)
    valve_a = ValveNode(name="V1", volume=(10, 5))
    valve_b = ValveNode(name="V2", volume=(10, 5))
    tank = TankNode(name="T", volume=0)

    connect(pump, valve_a, volume=1)
    connect(valve_a, valve_b, volume=1)
    connect(valve_b, tank, volume=1)

    graph.nodes = {"P": pump, "V1": valve_a, "V2": valve_b, "T": tank}
    return graph


class ExtractionLineNetworkStateTestCase(unittest.TestCase):
    def test_closed_valve_connector_does_not_inherit_other_side_state(self) -> None:
        class SceneStub:
            def __init__(self, items: list[object], by_name: dict[str, object]) -> None:
                self._items = items
                self._by_name = by_name

            def get_items(self) -> list[object]:
                return self._items

            def get_item(self, name: str) -> object | None:
                return self._by_name.get(name)

        class SourceStub:
            state = True
            default_color = (0.5, 0.5, 0.5)
            active_color = (0.0, 1.0, 0.0)

        connector = Connection((0, 0), (1, 0), name="C")
        connector.default_color = (1.0, 0.0, 0.0)
        connector.active_color = (0.0, 1.0, 0.0)
        connector.state = False

        valve = Switch(0, 0, name="V")
        valve.state = False
        valve.network_dominant_source_node = "SRC"
        valve.connections = [("left", connector)]

        source = SourceStub()
        scene = SceneStub([connector, valve], {"C": connector, "V": valve, "SRC": source})

        class CanvasStub:
            _propagate_connector_colors = ExtractionLineCanvas2D._propagate_connector_colors
            _connected_items_for_connector = ExtractionLineCanvas2D._connected_items_for_connector
            _fallback_connected_items = ExtractionLineCanvas2D._fallback_connected_items
            _preferred_connector_color_item = ExtractionLineCanvas2D._preferred_connector_color_item
            _connector_color_for_item = ExtractionLineCanvas2D._connector_color_for_item

        canvas = CanvasStub()
        canvas.scene = scene

        canvas._propagate_connector_colors()

        self.assertFalse(connector.state)
        self.assertEqual(connector.active_color, connector.default_color)

    def test_open_network_is_single_region(self) -> None:
        graph = make_graph()
        graph.set_valve_state("V1", True)
        graph.set_valve_state("V2", True)

        snapshot = graph.compute_state()

        self.assertEqual(snapshot.region_count, 1)
        self.assertEqual(snapshot.valves["V1"].region_id, snapshot.valves["V2"].region_id)

    def test_closed_valve_splits_region(self) -> None:
        graph = make_graph()
        graph.set_valve_state("V1", True)
        graph.set_valve_state("V2", False)

        snapshot = graph.compute_state()

        self.assertEqual(snapshot.region_count, 2)
        self.assertTrue(snapshot.valves["V2"].blocked_by_closed)
        self.assertEqual(snapshot.valves["V2"].region_volume, 16)
        self.assertEqual(snapshot.valves["V2"].valve_volume, 5)
        self.assertListEqual(snapshot.valves["V2"].side_volumes, [16])

    def test_dominant_source_precedence_prefers_pump(self) -> None:
        graph = ExtractionLineGraph()
        pump = PumpNode(name="P", volume=0)
        valve = ValveNode(name="V", volume=(10, 5))
        spectrometer = SpectrometerNode(name="S", volume=0)
        connect(pump, valve, volume=1)
        connect(valve, spectrometer, volume=1)
        graph.nodes = {"P": pump, "V": valve, "S": spectrometer}
        graph.set_valve_state("V", True)

        snapshot = graph.compute_state()
        rid = snapshot.valves["V"].region_id
        region = snapshot.regions[rid]

        self.assertEqual(region.dominant_source, "pump")
        self.assertEqual(region.dominant_source_node, "P")

    def test_equal_precedence_uses_explicit_tag_priority(self) -> None:
        graph = ExtractionLineGraph()
        pipette = PipetteNode(name="PIP", volume=0)
        valve = ValveNode(name="V", volume=(10, 5))
        laser = LaserNode(name="LAS", volume=0)
        connect(pipette, valve, volume=1)
        connect(valve, laser, volume=1)
        graph.nodes = {"LAS": laser, "V": valve, "PIP": pipette}
        graph.set_valve_state("V", True)

        snapshot = graph.compute_state()
        region = snapshot.regions[snapshot.valves["V"].region_id]

        self.assertEqual(region.dominant_source, "pipette")
        self.assertEqual(region.dominant_source_node, "PIP")

    def test_region_id_is_stable_across_node_order(self) -> None:
        graph_a = make_graph()
        graph_b = ExtractionLineGraph()
        pump = PumpNode(name="P", volume=0)
        valve_a = ValveNode(name="V1", volume=(10, 5))
        valve_b = ValveNode(name="V2", volume=(10, 5))
        tank = TankNode(name="T", volume=0)
        connect(pump, valve_a, volume=1)
        connect(valve_a, valve_b, volume=1)
        connect(valve_b, tank, volume=1)
        graph_b.nodes = {"T": tank, "V2": valve_b, "V1": valve_a, "P": pump}

        for graph in (graph_a, graph_b):
            graph.set_valve_state("V1", True)
            graph.set_valve_state("V2", True)

        snapshot_a = graph_a.compute_state()
        snapshot_b = graph_b.compute_state()

        self.assertEqual(snapshot_a.valves["V1"].region_id, snapshot_b.valves["V1"].region_id)
        self.assertEqual(snapshot_a.valves["V2"].region_id, snapshot_b.valves["V2"].region_id)

    def test_xml_and_yaml_loads_compute_equivalent_regions(self) -> None:
        xml_payload = (
            "<root>"
            "<pump>P</pump>"
            "<valve>V1<open_volume>10</open_volume><closed_volume>5</closed_volume></valve>"
            "<valve>V2<open_volume>10</open_volume><closed_volume>5</closed_volume></valve>"
            "<tank>T</tank>"
            "<connection><start>P</start><end>V1</end><volume>1</volume></connection>"
            "<connection><start>V1</start><end>V2</end><volume>1</volume></connection>"
            "<connection><start>V2</start><end>T</end><volume>1</volume></connection>"
            "</root>"
        )
        yaml_payload = json.dumps(
            {
                "turbo": [{"name": "P", "volume": 0}],
                "valve": [
                    {"name": "V1", "open_volume": 10, "closed_volume": 5},
                    {"name": "V2", "open_volume": 10, "closed_volume": 5},
                ],
                "tank": [{"name": "T", "volume": 0}],
                "connection": [
                    {"start": {"name": "P"}, "end": {"name": "V1"}, "volume": 1},
                    {"start": {"name": "V1"}, "end": {"name": "V2"}, "volume": 1},
                    {"start": {"name": "V2"}, "end": {"name": "T"}, "volume": 1},
                ],
            }
        )

        with tempfile.TemporaryDirectory() as root:
            xml_path = os.path.join(root, "canvas.xml")
            yaml_path = os.path.join(root, "canvas.yaml")
            with open(xml_path, "w") as wfile:
                wfile.write(xml_payload)
            with open(yaml_path, "w") as wfile:
                wfile.write(yaml_payload)

            xml_graph = ExtractionLineGraph()
            xml_graph.load(xml_path)
            xml_graph.set_valve_state("V1", True)
            xml_graph.set_valve_state("V2", True)
            xml_snapshot = xml_graph.compute_state()

            yaml_graph = ExtractionLineGraph()
            yaml_graph.load(yaml_path)
            yaml_graph.set_valve_state("V1", True)
            yaml_graph.set_valve_state("V2", True)
            yaml_snapshot = yaml_graph.compute_state()

        self.assertEqual(xml_snapshot.region_count, yaml_snapshot.region_count)
        self.assertEqual(sorted(xml_snapshot.regions.keys()), sorted(yaml_snapshot.regions.keys()))
        xml_volumes = sorted(region.volume for region in xml_snapshot.regions.values())
        yaml_volumes = sorted(region.volume for region in yaml_snapshot.regions.values())
        self.assertListEqual(xml_volumes, yaml_volumes)


if __name__ == "__main__":
    unittest.main()
