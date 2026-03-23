import unittest

try:
    from pychron.base_config_loadable import BaseConfigLoadable
except ModuleNotFoundError as e:
    BaseConfigLoadable = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


_BootstrapBase = BaseConfigLoadable if BaseConfigLoadable is not None else object


class _BootstrapHarness(_BootstrapBase):
    def __init__(
        self,
        load_result=True,
        open_result=True,
        initialize_result=True,
        post_initialize_error=None,
    ):
        self.name = "test-device"
        self.events = []
        self.messages = []
        self.load_result = load_result
        self.open_result = open_result
        self.initialize_result = initialize_result
        self.post_initialize_error = post_initialize_error

    def info(self, msg):
        self.messages.append(("info", msg))

    def warning(self, msg):
        self.messages.append(("warning", msg))

    def debug_exception(self):
        self.messages.append(("debug_exception", "called"))

    def load(self, *args, **kw):
        self.events.append("load")
        return self.load_result

    def open(self, *args, **kw):
        self.events.append("open")
        return self.open_result

    def initialize(self, *args, **kw):
        self.events.append("initialize")
        return self.initialize_result

    def post_initialize(self, *args, **kw):
        self.events.append("post_initialize")
        if self.post_initialize_error:
            raise self.post_initialize_error
        return True


@unittest.skipIf(BaseConfigLoadable is None, "PyYAML is not installed")
class DeviceBootstrapTestCase(unittest.TestCase):
    def test_bootstrap_result_records_successful_lifecycle(self):
        device = _BootstrapHarness()

        result = device.bootstrap_result(run_post_initialize=True)

        self.assertEqual(
            device.events, ["load", "open", "initialize", "post_initialize"]
        )
        self.assertTrue(result.success)
        self.assertTrue(result.compatible_success)
        self.assertEqual(result.failed_phase, "")

    def test_bootstrap_keeps_initialize_after_open_failure_for_compatibility(self):
        device = _BootstrapHarness(open_result=False)

        result = device.bootstrap_result(run_post_initialize=True)

        self.assertEqual(
            device.events, ["load", "open", "initialize", "post_initialize"]
        )
        self.assertFalse(result.success)
        self.assertTrue(result.compatible_success)
        self.assertFalse(result.opened)
        self.assertTrue(result.post_initialized)

    def test_bootstrap_result_flags_none_initialize_as_failure(self):
        device = _BootstrapHarness(initialize_result=None)

        result = device.bootstrap_result(run_post_initialize=True)

        self.assertEqual(device.events, ["load", "open", "initialize"])
        self.assertEqual(result.failed_phase, "initialize")
        self.assertEqual(result.error, "initialize returned None")
        self.assertFalse(result.compatible_success)

    def test_bootstrap_result_captures_post_initialize_exception(self):
        device = _BootstrapHarness(post_initialize_error=RuntimeError("boom"))

        result = device.bootstrap_result(run_post_initialize=True)

        self.assertEqual(
            device.events, ["load", "open", "initialize", "post_initialize"]
        )
        self.assertEqual(result.failed_phase, "post_initialize")
        self.assertEqual(result.error, "boom")
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
