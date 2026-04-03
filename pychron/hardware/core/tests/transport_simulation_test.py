import tempfile
import unittest

try:
    from pychron.hardware.actuators.pychron_gp_actuator import PychronGPActuator
    from pychron.hardware.core.communicators.ethernet_communicator import (
        EthernetCommunicator,
    )
    from pychron.hardware.core.communicators.serial_communicator import SerialCommunicator
    from pychron.hardware.core.simulation import (
        FaultPolicy,
        NGXSimulatorProtocol,
        PychronValveSimulatorProtocol,
        RecordingTransportAdapter,
        ReplayTransportAdapter,
        SimulatorTransportAdapter,
        TransportDisconnectError,
        TransportEvent,
        TransportSession,
        TransportTimeoutError,
        load_transport_session,
    )
    from pychron.hardware.isotopx_spectrometer_controller import NGXController
    from pychron.spectrometer.isotopx.spectrometer.ngx import NGXSpectrometer
except ModuleNotFoundError as exc:
    PychronGPActuator = None
    EthernetCommunicator = None
    FaultPolicy = None
    NGXController = None
    NGXSimulatorProtocol = None
    NGXSpectrometer = None
    PychronValveSimulatorProtocol = None
    RecordingTransportAdapter = None
    ReplayTransportAdapter = None
    SerialCommunicator = None
    SimulatorTransportAdapter = None
    TransportDisconnectError = None
    TransportEvent = None
    TransportSession = None
    TransportTimeoutError = None
    load_transport_session = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _DummyDetector:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind


class _DummyValve:
    name = "V-A"
    check_actuation_enabled = True
    check_actuation_delay = 0


@unittest.skipIf(_IMPORT_ERROR is not None, "Traits stack not available")
class TransportSimulationTestCase(unittest.TestCase):
    def test_serial_strict_replay_ask(self):
        session = TransportSession(transport_kind="serial")
        session.append(
            TransportEvent(
                event_type="exchange",
                request_payload="PING",
                response_payload="PONG\r",
            )
        )
        communicator = SerialCommunicator()
        communicator.set_transport_adapter(ReplayTransportAdapter(session))
        communicator.open()

        response = communicator.ask("PING", verbose=False)

        self.assertEqual(response, "PONG")

    def test_recording_adapter_round_trip(self):
        adapter = SimulatorTransportAdapter(
            "serial", PychronValveSimulatorProtocol(), fault_policy=FaultPolicy()
        )
        recorder = RecordingTransportAdapter(
            adapter, session=TransportSession(transport_kind="serial")
        )
        recorder.open()
        recorder.request("GetValveState A")

        with tempfile.NamedTemporaryFile(suffix=".json") as fp:
            recorder.session.save(fp.name)
            loaded = load_transport_session(fp.name)

        self.assertEqual(len(loaded.events), 2)
        self.assertEqual(loaded.events[1].request_payload, "GetValveState A")

    def test_timeout_fault_propagates(self):
        communicator = SerialCommunicator()
        communicator.set_transport_adapter(
            SimulatorTransportAdapter(
                "serial",
                PychronValveSimulatorProtocol(),
                fault_policy=FaultPolicy(
                    [{"fault": "timeout", "match": "GetValveState A"}]
                ),
            )
        )
        communicator.open()

        with self.assertRaises(TransportTimeoutError):
            communicator.ask("GetValveState A", verbose=False)

    def test_malformed_out_of_range_and_disconnect_faults(self):
        adapter = SimulatorTransportAdapter(
            "serial",
            PychronValveSimulatorProtocol(),
            fault_policy=FaultPolicy(
                [
                    {
                        "fault": "malformed_packet",
                        "match": "GetValveState A",
                        "nth": 1,
                        "response_payload": "<<BAD>>",
                    },
                    {
                        "fault": "out_of_range_values",
                        "match": "GetValveState A",
                        "nth": 2,
                        "response_payload": "999999",
                    },
                    {
                        "fault": "intermittent_disconnect",
                        "match": "GetValveState A",
                        "nth": 3,
                    },
                ]
            ),
        )
        adapter.open()

        self.assertEqual(adapter.request("GetValveState A"), "<<BAD>>")
        self.assertEqual(adapter.request("GetValveState A"), "999999")
        with self.assertRaises(TransportDisconnectError):
            adapter.request("GetValveState A")
        self.assertFalse(adapter.connected)

    def test_stale_status_fault_repeats_previous_state(self):
        adapter = SimulatorTransportAdapter(
            "serial",
            PychronValveSimulatorProtocol(),
            fault_policy=FaultPolicy(
                [{"fault": "stale_status", "match": "GetValveState A", "nth": 2}]
            ),
        )
        adapter.open()
        adapter.request("Open A")

        first = adapter.request("GetValveState A")
        adapter.request("Close A")
        second = adapter.request("GetValveState A")

        self.assertEqual(first, "True")
        self.assertEqual(second, "True")

    def test_pychron_valve_simulator_end_to_end(self):
        actuator = PychronGPActuator(name="sim-actuator")
        communicator = SerialCommunicator()
        communicator.set_transport_adapter(
            SimulatorTransportAdapter("serial", PychronValveSimulatorProtocol())
        )
        communicator.open()
        actuator.communicator = communicator
        valve = _DummyValve()

        self.assertTrue(actuator.open_channel(valve))
        self.assertTrue(actuator.get_channel_state(valve))
        self.assertTrue(actuator.close_channel(valve))
        self.assertFalse(actuator.get_channel_state(valve))

    def test_ngx_simulator_end_to_end(self):
        controller = NGXController(name="ngx-controller")
        communicator = EthernetCommunicator()
        communicator.set_transport_adapter(
            SimulatorTransportAdapter("tcp", NGXSimulatorProtocol(seed=7))
        )
        communicator.open()
        controller.communicator = communicator

        spec = NGXSpectrometer()
        spec.rcs_id = "NOM"
        spec.integration_time = 1
        spec.microcontroller = controller
        spec.detectors = [
            _DummyDetector("H2", "Faraday"),
            _DummyDetector("CDD", "CDD"),
            _DummyDetector("L2", "Faraday"),
        ]

        keys, signals, collection_time, inc = spec.read_intensities(
            trigger=True, timeout=5, verbose=False
        )

        self.assertTrue(inc)
        self.assertEqual(len(keys), 3)
        self.assertEqual(len(signals), 3)
        self.assertEqual(keys, ["L2", "CDD", "H2"])
        self.assertIsNotNone(collection_time)


if __name__ == "__main__":
    unittest.main()
