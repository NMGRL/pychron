import unittest
from contextlib import nullcontext
from types import SimpleNamespace

try:
    from pychron.experiment.automated_run.automated_run import AutomatedRun
    from pychron.experiment.automated_run.data_collector import DataCollector
    from pychron.pychron_constants import FAILED
except ModuleNotFoundError as exc:
    AutomatedRun = None
    DataCollector = None
    FAILED = "failed"
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class _RunStub:
    def __init__(self):
        self.calls = []

    def cancel_run(self, **kw):
        self.calls.append(kw)


class _CollectorStub:
    def __init__(self):
        self.terminated = False
        self.canceled = True
        self.err_message = "boom"

    def trait_set(self, **kw):
        self.kw = kw

    def set_starttime(self, starttime):
        self.starttime = starttime

    def measure(self):
        return None


class MeasurementFailureHandlingTestCase(unittest.TestCase):
    @unittest.skipIf(IMPORT_ERROR is not None, f"missing dependency: {IMPORT_ERROR}")
    def test_data_collector_iteration_exception_fails_run(self):
        collector = DataCollector()
        run = _RunStub()
        collector.automated_run = run
        collector._get_data = lambda detectors=None: (_ for _ in ()).throw(
            ValueError("shape mismatch")
        )

        result = collector._iteration(1)

        self.assertIsNone(result)
        self.assertTrue(collector.canceled)
        self.assertIn("shape mismatch", collector.err_message)
        self.assertEqual(
            run.calls,
            [{"state": FAILED, "do_post_equilibration": False}],
        )

    @unittest.skipIf(IMPORT_ERROR is not None, f"missing dependency: {IMPORT_ERROR}")
    def test_measure_preserves_failed_state_for_canceled_collector(self):
        run = AutomatedRun()
        run.measurement_script = SimpleNamespace()
        run.spectrometer_manager = SimpleNamespace(
            spectrometer=SimpleNamespace(get_update_period=lambda it: 1)
        )
        run.multi_collector = _CollectorStub()
        run.is_peak_hop = False
        run._active_detectors = []
        run.experiment_type = "signal"
        run._integration_seconds = 1
        run.spec = SimpleNamespace(state=FAILED, analysis_type="unknown")
        run.persister = SimpleNamespace(writer_ctx=lambda: nullcontext())
        run._update_persister_spec = lambda **kw: None

        cancel_calls = []
        run.cancel_run = lambda *args, **kw: cancel_calls.append((args, kw))

        result = run._measure(
            grpname="signal",
            data_writer=lambda *args, **kw: None,
            ncounts=1,
            starttime=0,
            starttime_offset=0,
            series=0,
            check_conditionals=False,
            color="black",
        )

        self.assertFalse(result)
        self.assertEqual(cancel_calls, [])


if __name__ == "__main__":
    unittest.main()
