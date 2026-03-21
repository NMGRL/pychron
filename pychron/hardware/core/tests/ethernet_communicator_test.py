import unittest

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


if __name__ == "__main__":
    unittest.main()
