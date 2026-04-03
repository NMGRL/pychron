import tempfile
import unittest

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


class SimulationCoreTestCase(unittest.TestCase):
    def test_strict_replay_returns_expected_response(self):
        session = TransportSession(transport_kind="serial")
        session.append(
            TransportEvent(
                event_type="exchange", request_payload="PING", response_payload="PONG"
            )
        )
        adapter = ReplayTransportAdapter(session)
        adapter.open()

        self.assertEqual(adapter.request("PING"), "PONG")

    def test_recording_adapter_serializes_session(self):
        wrapped = SimulatorTransportAdapter("serial", PychronValveSimulatorProtocol())
        recorder = RecordingTransportAdapter(
            wrapped, session=TransportSession(transport_kind="serial")
        )
        recorder.open()
        recorder.request("GetValveState A")

        with tempfile.NamedTemporaryFile(suffix=".json") as fp:
            recorder.session.save(fp.name)
            loaded = load_transport_session(fp.name)

        self.assertEqual(loaded.events[1].request_payload, "GetValveState A")

    def test_timeout_and_disconnect_faults_raise(self):
        timeout_adapter = SimulatorTransportAdapter(
            "serial",
            PychronValveSimulatorProtocol(),
            fault_policy=FaultPolicy([{"fault": "timeout", "match": "GetValveState"}]),
        )
        timeout_adapter.open()
        with self.assertRaises(TransportTimeoutError):
            timeout_adapter.request("GetValveState A")

        disconnect_adapter = SimulatorTransportAdapter(
            "serial",
            PychronValveSimulatorProtocol(),
            fault_policy=FaultPolicy(
                [{"fault": "intermittent_disconnect", "match": "GetValveState"}]
            ),
        )
        disconnect_adapter.open()
        with self.assertRaises(TransportDisconnectError):
            disconnect_adapter.request("GetValveState A")
        self.assertFalse(disconnect_adapter.connected)

    def test_stale_and_out_of_range_faults_override_response(self):
        adapter = SimulatorTransportAdapter(
            "serial",
            PychronValveSimulatorProtocol(),
            fault_policy=FaultPolicy(
                [
                    {"fault": "stale_status", "match": "GetValveState A", "nth": 2},
                    {
                        "fault": "out_of_range_values",
                        "match": "GetValveState B",
                        "response_payload": "999999",
                    },
                ]
            ),
        )
        adapter.open()
        adapter.request("Open A")
        self.assertEqual(adapter.request("GetValveState A"), "True")
        adapter.request("Close A")
        self.assertEqual(adapter.request("GetValveState A"), "True")
        self.assertEqual(adapter.request("GetValveState B"), "999999")

    def test_ngx_simulator_protocol_emits_deterministic_acquisition_event(self):
        adapter = SimulatorTransportAdapter("tcp", NGXSimulatorProtocol(seed=5))
        adapter.open()

        response = adapter.request("StartAcq 1,NOM\r")
        event = adapter.readline("#\r\n")

        self.assertEqual(response, "E00")
        self.assertTrue(event.startswith("#EVENT:ACQ,NOM,"))
        self.assertTrue(event.endswith("#\r\n"))


if __name__ == "__main__":
    unittest.main()
