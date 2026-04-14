import unittest
import json
import tempfile
from pathlib import Path

try:
    from pychron.hardware.core.communicators.ethernet_communicator import (
        EthernetCommunicator,
        MessageFrame,
        TCPHandler,
        UDPHandler,
    )
except ModuleNotFoundError as exc:
    EthernetCommunicator = None
    MessageFrame = None
    TCPHandler = None
    UDPHandler = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.span import set_global_recorder


class _FakeSocket:
    def __init__(self, recv_chunks=None):
        self.recv_chunks = list(recv_chunks or [])
        self.sent = []
        self.closed = False

    def sendall(self, payload):
        self.sent.append(payload)

    def recv(self, datasize):
        if self.recv_chunks:
            return self.recv_chunks.pop(0)
        return b""

    def recvfrom(self, datasize):
        if self.recv_chunks:
            return self.recv_chunks.pop(0), ("127.0.0.1", 1000)
        return b"", ("127.0.0.1", 1000)

    def close(self):
        self.closed = True


@unittest.skipIf(_IMPORT_ERROR is not None, "Traits stack not available")
class EthernetCommunicatorTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "ethernet-io.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        TelemetryContext.clear()
        TelemetryContext.set_queue_id("queue_1")
        TelemetryContext.set_trace_id("trace_1")
        TelemetryContext.set_run_id("run_1")
        set_global_recorder(self.recorder)

    def tearDown(self):
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_tcp_handler_uses_sendall(self):
        handler = TCPHandler()
        handler.sock = _FakeSocket()

        handler.send_packet("PING")

        self.assertEqual(handler.sock.sent, [b"PING"])

    def test_udp_handler_respects_message_frame(self):
        payload = b"0004TEST"
        handler = UDPHandler()
        handler.sock = _FakeSocket(recv_chunks=[payload])
        handler.message_frame = MessageFrame(message_len=True, nmessage_len=4)

        response = handler.get_packet(message_frame=handler.message_frame)

        self.assertEqual(response, "TEST")

    def test_reset_closes_read_and_write_handlers(self):
        communicator = EthernetCommunicator()
        communicator.handler = TCPHandler()
        write_sock = _FakeSocket()
        communicator.handler.sock = write_sock
        communicator.read_handler = UDPHandler()
        read_sock = _FakeSocket()
        communicator.read_handler.sock = read_sock

        communicator.reset()

        self.assertTrue(write_sock.closed)
        self.assertTrue(read_sock.closed)
        self.assertIsNone(communicator.handler)
        self.assertIsNone(communicator.read_handler)

    def test_ask_records_start_and_end_device_io_events(self):
        communicator = EthernetCommunicator(name="spec_comm")
        communicator.kind = "TCP"
        communicator.host = "127.0.0.1"
        communicator.port = 8000
        communicator.simulation = False
        communicator.write_terminator = "\r"
        communicator.log_response = lambda *args, **kw: None
        communicator._ask = lambda *args, **kw: "OK"

        result = communicator.ask("GetData", verbose=False)

        self.recorder.flush()
        with open(self.log_path) as rfile:
            events = [json.loads(line) for line in rfile.readlines()]

        self.assertEqual(result, "OK")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["payload"]["stage"], "start")
        self.assertEqual(events[1]["payload"]["stage"], "end")
        self.assertEqual(events[1]["payload"]["success"], True)

    def test_repeated_failures_call_health_failure_callback(self):
        communicator = EthernetCommunicator(name="spec_comm")
        failures = []
        communicator.health_failure_callback = lambda operation, **kw: failures.append(
            (operation, kw.get("error"))
        )
        communicator._ask = lambda *args, **kw: None
        communicator.kind = "TCP"
        communicator.host = "127.0.0.1"
        communicator.port = 8000
        communicator.simulation = False
        communicator.write_terminator = "\r"
        communicator.log_response = lambda *args, **kw: None

        communicator.ask("GetData", verbose=False)

        self.assertEqual(failures[-1][0], "ask")
        self.assertIn("Connection refused", failures[-1][1])

    def test_successful_write_calls_health_success_callback(self):
        communicator = EthernetCommunicator(name="spec_comm")
        successes = []
        communicator.health_success_callback = lambda operation, **kw: successes.append(operation)
        communicator.kind = "TCP"
        communicator.host = "127.0.0.1"
        communicator.port = 8000
        communicator.handler = TCPHandler()
        communicator.handler.sock = _FakeSocket()
        communicator.handler.address = ("127.0.0.1", 8000)
        communicator.log_tell = lambda *args, **kw: None

        communicator.tell("PING", verbose=False)

        self.assertEqual(successes[-1], "tell")


if __name__ == "__main__":
    unittest.main()
