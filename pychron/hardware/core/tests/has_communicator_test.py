import unittest

from pychron.has_communicator import HasCommunicator


class _FakeCommunicator:
    def __init__(self):
        self.open_calls = []
        self.closed = False
        self.reported = False

    def open(self, **kw):
        self.open_calls.append(kw)
        return True

    def close(self):
        self.closed = True

    def report(self):
        self.reported = True

    def ask(self, *args, **kw):
        return args, kw


class _HasCommunicatorHarness(HasCommunicator):
    def __init__(self):
        self.name = "device"
        self.info_messages = []
        self.warning_messages = []
        self.communicator = None

    def _communicator_factory(self, communicator_type):
        return _FakeCommunicator()

    def info(self, msg):
        self.info_messages.append(msg)

    def warning(self, msg):
        self.warning_messages.append(msg)

    def debug_exception(self):
        return


class HasCommunicatorTestCase(unittest.TestCase):
    def test_build_communicator_assigns_instance(self):
        device = _HasCommunicatorHarness()

        communicator = device.build_communicator("ethernet")

        self.assertIs(device.communicator, communicator)

    def test_create_communicator_opens_instance(self):
        device = _HasCommunicatorHarness()

        communicator = device.create_communicator("ethernet", timeout=1)

        self.assertEqual(communicator.open_calls, [{"timeout": 1}])
        self.assertIs(device.communicator, communicator)

    def test_require_communicator_reports_missing_instance(self):
        device = _HasCommunicatorHarness()

        communicator = device.require_communicator("ask")

        self.assertIsNone(communicator)
        self.assertEqual(device.info_messages, ["no communicator configured for ask device"])

    def test_open_reports_after_opening(self):
        device = _HasCommunicatorHarness()
        communicator = device.build_communicator("ethernet")

        result = device.open(timeout=2)

        self.assertTrue(result)
        self.assertEqual(communicator.open_calls, [{"timeout": 2}])
        self.assertTrue(communicator.reported)


if __name__ == "__main__":
    unittest.main()
