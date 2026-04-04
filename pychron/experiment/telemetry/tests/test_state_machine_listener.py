"""Tests for state machine telemetry listener."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.state_machine_listener import StateMachineListener
from pychron.experiment.telemetry.context import TelemetryContext


class TestStateMachineListener(unittest.TestCase):
    """Test StateMachineListener for state machine transitions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        self.listener = StateMachineListener(self.recorder)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def _make_transition_record(
        self,
        state_from: str = "idle",
        state_to: str = "running",
        reason: str = "user_started",
        accepted: bool = True,
        source: str = "controller.execute",
    ) -> Mock:
        """Helper to create a mock TransitionRecord."""
        record = Mock()
        record.state_from = state_from
        record.state_to = state_to
        record.reason = reason
        record.accepted = accepted
        record.source = source
        record.ts = None
        record.run_id = None
        record.run_uuid = None
        return record

    def test_listener_emits_transition_event(self):
        """Test that listener emits a transition event."""
        record = self._make_transition_record()

        self.listener.on_transition("executor", record)
        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)

        import json

        event_data = json.loads(lines[0])
        event = TelemetryEvent(**event_data)

        self.assertEqual(event.event_type, "state_transition")
        self.assertEqual(event.component, "executor")
        self.assertEqual(event.state_from, "idle")
        self.assertEqual(event.state_to, "running")

    def test_listener_captures_accepted_flag(self):
        """Test that listener captures accepted vs. rejected transitions."""
        record_accepted = self._make_transition_record(accepted=True)
        record_rejected = self._make_transition_record(accepted=False)

        self.listener.on_transition("executor", record_accepted)
        self.listener.on_transition("executor", record_rejected)
        self.recorder.flush()

        import json

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        event1 = TelemetryEvent(**json.loads(lines[0]))
        event2 = TelemetryEvent(**json.loads(lines[1]))

        self.assertTrue(event1.accepted)
        self.assertFalse(event2.accepted)

    def test_listener_propagates_context_ids(self):
        """Test that listener includes queue and trace IDs."""
        record = self._make_transition_record()

        self.listener.on_transition("queue", record)
        self.recorder.flush()

        import json

        with open(self.log_path) as f:
            lines = f.readlines()

        event_data = json.loads(lines[0])

        self.assertEqual(event_data["queue_id"], "test_queue")
        self.assertEqual(event_data["trace_id"], "trace_123")

    def test_listener_records_machine_name(self):
        """Test that listener records which machine transitioned."""
        machines = ["executor", "queue", "run"]

        for machine in machines:
            record = self._make_transition_record()
            self.listener.on_transition(machine, record)

        self.recorder.flush()

        import json

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 3)

        for i, machine in enumerate(machines):
            event = TelemetryEvent(**json.loads(lines[i]))
            self.assertEqual(event.component, machine)

    def test_listener_with_run_context(self):
        """Test that listener includes run context from context variables."""
        TelemetryContext.set_run_id("sample-001-00-00")
        TelemetryContext.set_run_uuid("550e8400-e29b-41d4-a716-446655440000")

        record = self._make_transition_record()
        self.listener.on_transition("run", record)
        self.recorder.flush()

        import json

        with open(self.log_path) as f:
            lines = f.readlines()

        event_data = json.loads(lines[0])

        self.assertEqual(event_data["run_id"], "sample-001-00-00")
        self.assertEqual(event_data["run_uuid"], "550e8400-e29b-41d4-a716-446655440000")


if __name__ == "__main__":
    unittest.main()
