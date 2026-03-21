import unittest

try:
    from pychron.experiment.automated_run.spec import (
        AutomatedRunSpec,
        NOT_RUN,
        EXTRACTION,
        MEASUREMENT,
        SUCCESS,
        FAILED,
        TRUNCATED,
        CANCELED,
        ABORTED,
    )
except ModuleNotFoundError as exc:
    AutomatedRunSpec = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class AutomatedRunStateMachineTestCase(unittest.TestCase):
    def test_nominal_transition_path(self):
        spec = AutomatedRunSpec(labnumber="10000")

        self.assertTrue(spec.set_state(EXTRACTION))
        self.assertTrue(spec.set_state(MEASUREMENT))
        self.assertTrue(spec.set_state(SUCCESS))
        self.assertEqual(spec.state, SUCCESS)

    def test_terminal_state_rejects_non_forced_transition(self):
        spec = AutomatedRunSpec(labnumber="10000")
        spec.set_state(FAILED, force=True)

        self.assertFalse(spec.set_state(MEASUREMENT))
        self.assertEqual(spec.state, FAILED)

    def test_truncated_can_complete_successfully(self):
        spec = AutomatedRunSpec(labnumber="10000")
        spec.set_state(EXTRACTION)
        spec.set_state(MEASUREMENT)
        spec.set_state(TRUNCATED, force=True)

        self.assertTrue(spec.set_state(SUCCESS))
        self.assertEqual(spec.state, SUCCESS)

    def test_terminated_alias_maps_to_failed(self):
        spec = AutomatedRunSpec(labnumber="10000")
        spec.set_state(EXTRACTION)

        self.assertTrue(spec.set_state("terminated", force=True))
        self.assertEqual(spec.state, FAILED)

    def test_not_run_reset_requires_force(self):
        spec = AutomatedRunSpec(labnumber="10000")
        spec.set_state(EXTRACTION)

        self.assertFalse(spec.set_state(NOT_RUN))
        self.assertTrue(spec.set_state(NOT_RUN, force=True))
        self.assertEqual(spec.state, NOT_RUN)

    def test_abort_is_terminal(self):
        spec = AutomatedRunSpec(labnumber="10000")

        spec.set_state(ABORTED, force=True)
        self.assertTrue(spec.is_terminal_state())
        self.assertFalse(spec.set_state(CANCELED))


if __name__ == "__main__":
    unittest.main()
