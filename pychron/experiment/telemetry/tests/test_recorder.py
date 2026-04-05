"""Tests for TelemetryRecorder JSONL writing."""

import json
import tempfile
import unittest
from pathlib import Path
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.recorder import TelemetryRecorder


class TestTelemetryRecorder(unittest.TestCase):
    """Test TelemetryRecorder for JSONL output."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_record_single_event(self):
        """Test recording a single event."""
        log_path = self.temp_path / "test.jsonl"

        with TelemetryRecorder(log_path) as recorder:
            event = TelemetryEvent.create(event_type="test", component="test", queue_id="queue1")
            recorder.record_event(event)

        # File should exist and contain one line
        self.assertTrue(log_path.exists())
        with open(log_path) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)

        # Should be valid JSON
        data = json.loads(lines[0])
        self.assertEqual(data["event_type"], "test")
        self.assertEqual(data["queue_id"], "queue1")

    def test_record_multiple_events(self):
        """Test recording multiple events."""
        log_path = self.temp_path / "test.jsonl"

        with TelemetryRecorder(log_path, max_buffer_size=10) as recorder:
            for i in range(5):
                event = TelemetryEvent.create(
                    event_type="test", component="test", payload={"index": i}
                )
                recorder.record_event(event)

        with open(log_path) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 5)

        # Verify each event
        for i, line in enumerate(lines):
            data = json.loads(line)
            self.assertEqual(data["payload"]["index"], i)

    def test_auto_flush_on_buffer_full(self):
        """Test that buffer flushes when full."""
        log_path = self.temp_path / "test.jsonl"

        recorder = TelemetryRecorder(log_path, max_buffer_size=3)

        # Add 3 events (should not flush yet)
        for i in range(3):
            event = TelemetryEvent.create(event_type="test", component="test", payload={"index": i})
            recorder.record_event(event)

        # Add one more (should trigger flush)
        event = TelemetryEvent.create(event_type="test", component="test", payload={"index": 3})
        recorder.record_event(event)

        # At this point, events should be on disk
        with open(log_path) as f:
            lines = f.readlines()
        self.assertGreaterEqual(len(lines), 3)  # At least first 3

        recorder.close()

    def test_for_queue_factory(self):
        """Test factory method for queue telemetry."""
        recorder = TelemetryRecorder.for_queue("test_experiment", log_root=self.temp_path)

        # Should create file with expected naming
        self.assertTrue(
            recorder.log_path.exists() or str(recorder.log_path).startswith(str(self.temp_path))
        )
        self.assertIn("test_experiment", str(recorder.log_path))
        self.assertTrue(str(recorder.log_path).endswith(".jsonl"))

        recorder.close()

    def test_creates_directory_if_missing(self):
        """Test that recorder creates directory structure."""
        log_path = self.temp_path / "nested" / "deep" / "test.jsonl"

        with TelemetryRecorder(log_path) as recorder:
            event = TelemetryEvent.create(event_type="test", component="test")
            recorder.record_event(event)

        self.assertTrue(log_path.exists())
        self.assertTrue(log_path.parent.exists())

    def test_context_manager(self):
        """Test using recorder as context manager."""
        log_path = self.temp_path / "test.jsonl"

        with TelemetryRecorder(log_path) as recorder:
            event = TelemetryEvent.create(event_type="test", component="test")
            recorder.record_event(event)

        # File should be closed and flushed
        self.assertTrue(log_path.exists())
        with open(log_path) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
