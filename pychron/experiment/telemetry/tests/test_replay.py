"""Tests for telemetry replay and incident reporting."""

import json
import tempfile
import unittest
from pathlib import Path
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.replay import load_telemetry_log, replay_queue_telemetry


class TestTelemetryReplay(unittest.TestCase):
    """Test telemetry log replay and incident report generation."""

    def setUp(self):
        """Create test telemetry log file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_file = self.temp_path / "test.jsonl"

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def _write_events(self, events):
        """Helper to write events to log file."""
        with open(self.log_file, "w") as f:
            for event in events:
                if isinstance(event, dict):
                    json_str = json.dumps(event)
                else:
                    json_str = json.dumps(event.to_dict(), default=str)
                f.write(json_str + "\n")

    def test_load_telemetry_log_basic(self):
        """Test loading events from telemetry log."""
        events = [
            TelemetryEvent.create(event_type="test", component="test"),
            TelemetryEvent.create(event_type="test", component="test"),
        ]
        self._write_events(events)

        loaded = list(load_telemetry_log(self.log_file))
        self.assertEqual(len(loaded), 2)
        self.assertTrue(all(isinstance(e, TelemetryEvent) for e in loaded))

    def test_load_telemetry_log_file_not_found(self):
        """Test error when file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            list(load_telemetry_log(self.temp_path / "nonexistent.jsonl"))

    def test_replay_queue_telemetry_basic(self):
        """Test basic queue replay."""
        events = [
            TelemetryEvent.create(
                event_type="telemetry_session_start",
                component="executor",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="state_transition",
                component="executor_machine",
                state_from="idle",
                state_to="preparing",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="state_transition",
                component="executor_machine",
                state_from="preparing",
                state_to="running_queue",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
        ]
        self._write_events(events)

        report = replay_queue_telemetry(self.log_file)

        self.assertEqual(report.queue_id, "test_queue")
        self.assertEqual(report.trace_id, "trace_123")
        self.assertGreater(len(report.timeline), 0)

    def test_replay_state_machine_history(self):
        """Test that state transitions are captured in replay."""
        events = [
            TelemetryEvent.create(
                event_type="telemetry_session_start",
                component="executor",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="state_transition",
                component="queue_machine",
                state_from="queue_idle",
                state_to="ready",
                queue_id="test_queue",
                trace_id="trace_123",
                accepted=True,
            ),
            TelemetryEvent.create(
                event_type="state_transition",
                component="queue_machine",
                state_from="ready",
                state_to="completed",
                queue_id="test_queue",
                trace_id="trace_123",
                accepted=True,
            ),
        ]
        self._write_events(events)

        report = replay_queue_telemetry(self.log_file)

        # Should have state machine history
        self.assertIn("queue_machine", report.state_machine_history)
        transitions = report.state_machine_history["queue_machine"]
        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].state_to, "ready")
        self.assertEqual(transitions[1].state_to, "completed")

    def test_replay_device_commands(self):
        """Test that device commands are captured."""
        events = [
            TelemetryEvent.create(
                event_type="telemetry_session_start",
                component="executor",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="device_command",
                component="extraction_line",
                action="extract",
                queue_id="test_queue",
                trace_id="trace_123",
                success=True,
                duration_ms=1000,
            ),
        ]
        self._write_events(events)

        report = replay_queue_telemetry(self.log_file)

        self.assertGreater(len(report.device_commands), 0)
        cmd = report.device_commands[0]
        self.assertEqual(cmd["component"], "extraction_line")
        self.assertEqual(cmd["action"], "extract")
        self.assertTrue(cmd["success"])

    def test_replay_monitor_events(self):
        """Test that monitor/interlock events are captured."""
        events = [
            TelemetryEvent.create(
                event_type="telemetry_session_start",
                component="executor",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="monitor_check",
                component="monitor",
                action="check",
                queue_id="test_queue",
                trace_id="trace_123",
                payload={"condition": "temperature", "value": 100},
            ),
            TelemetryEvent.create(
                event_type="interlock_check",
                component="interlock",
                queue_id="test_queue",
                trace_id="trace_123",
                payload={"result": "allow"},
            ),
        ]
        self._write_events(events)

        report = replay_queue_telemetry(self.log_file)

        self.assertGreater(len(report.monitor_history), 0)

    def test_replay_summary_generation(self):
        """Test that replay generates human-readable summary."""
        events = [
            TelemetryEvent.create(
                event_type="telemetry_session_start",
                component="executor",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
            TelemetryEvent.create(
                event_type="state_transition",
                component="executor_machine",
                state_from="idle",
                state_to="completed",
                queue_id="test_queue",
                trace_id="trace_123",
            ),
        ]
        self._write_events(events)

        report = replay_queue_telemetry(self.log_file)

        self.assertIsNotNone(report.summary)
        self.assertIn("test_queue", report.summary)
        self.assertIn("trace_123", report.summary)


if __name__ == "__main__":
    unittest.main()
