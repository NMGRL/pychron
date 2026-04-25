import json
import tempfile
import time
import unittest
from pathlib import Path

from traits.api import HasTraits, Str

try:
    from pychron.experiment.experiment_executor import ExperimentExecutor
except ModuleNotFoundError as exc:
    ExperimentExecutor = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.recorder import TelemetryRecorder


class _FakeQueue(HasTraits):
    name = Str("diagnostic_queue")


class _FakeRunSpec:
    state = "measurement"


class _FakeRun:
    runid = "10001-01"
    uuid = "run-uuid-1"
    spec = _FakeRunSpec()


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class ExperimentExecutorDiagnosticsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "executor-diagnostics.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        self.executor = ExperimentExecutor()
        self.executor._controller.telemetry_recorder = self.recorder
        self.executor.experiment_queue = _FakeQueue()
        self.executor.alive = True
        self.executor.diagnostic_stall_timeout = 0.01
        self.executor.diagnostic_progress_interval = 0.01
        TelemetryContext.clear()
        TelemetryContext.set_queue_id("diagnostic_queue")
        TelemetryContext.set_trace_id("trace-1")
        TelemetryContext.set_run_id("10001-01")
        TelemetryContext.set_run_uuid("run-uuid-1")

    def tearDown(self) -> None:
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def _read_events(self) -> list[TelemetryEvent]:
        self.recorder.flush()
        with open(self.log_path) as rfile:
            return [TelemetryEvent(**json.loads(line)) for line in rfile.readlines()]

    def test_mark_progress_records_execution_progress_event(self) -> None:
        self.executor._mark_progress("run.step.enter", run=_FakeRun(), step="measurement")

        events = self._read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "execution_progress")
        self.assertEqual(events[0].action, "run.step.enter")
        self.assertEqual(events[0].payload["queue_name"], "diagnostic_queue")
        self.assertEqual(events[0].payload["run_id"], "10001-01")

    def test_stall_snapshot_records_without_mutating_executor_state(self) -> None:
        self.executor._last_progress_marker = "run.measurement.enter"
        self.executor._last_progress_timestamp = time.time() - 1

        self.executor._maybe_emit_stall_snapshot("measurement.wait", run=_FakeRun(), force=False)

        events = self._read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "stall_snapshot")
        self.assertEqual(events[0].payload["last_progress_marker"], "run.measurement.enter")
        self.assertTrue(self.executor.alive)


if __name__ == "__main__":
    unittest.main()
