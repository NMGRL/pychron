"""Tests for Span telemetry context manager."""

import tempfile
import time
import unittest
from pathlib import Path
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.span import Span, set_global_recorder
from pychron.experiment.telemetry.context import TelemetryContext


class TestSpan(unittest.TestCase):
    """Test Span context manager for timed operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Create recorder
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        set_global_recorder(self.recorder)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_span_records_start_and_end(self):
        """Test that span records both start and end events."""
        with Span("span_1", "test", "test_action"):
            time.sleep(0.01)  # Small delay to get non-zero duration

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        # Should have 2 events: span_start and span_end
        self.assertEqual(len(lines), 2)

        start_event = TelemetryEvent(**__import__("json").loads(lines[0]))
        end_event = TelemetryEvent(**__import__("json").loads(lines[1]))

        self.assertEqual(start_event.event_type, "span_start")
        self.assertEqual(end_event.event_type, "span_end")

    def test_span_timing(self):
        """Test that span records elapsed time."""
        sleep_time = 0.05  # 50ms

        with Span("span_1", "test", "test_action") as span:
            time.sleep(sleep_time)

        # Duration should be approximately sleep_time (in ms)
        self.assertIsNotNone(span.duration_ms)
        self.assertGreaterEqual(span.duration_ms, sleep_time * 1000 * 0.8)  # Allow 20% variance

    def test_span_success_flag(self):
        """Test that span records success status."""
        with Span("span_1", "test", "test_action") as span:
            pass

        self.assertTrue(span.success)
        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        end_event = TelemetryEvent(**__import__("json").loads(lines[1]))
        self.assertTrue(end_event.success)

    def test_span_failure_flag(self):
        """Test that span records failure status."""
        span = Span("span_1", "test", "test_action")
        span.__enter__()
        span.record_failure(reason="test_failure", error="Test error message")

        self.assertFalse(span.success)
        self.assertEqual(span.error, "Test error message")
        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        end_event = TelemetryEvent(**__import__("json").loads(lines[1]))
        self.assertFalse(end_event.success)
        self.assertEqual(end_event.error, "Test error message")

    def test_span_nesting(self):
        """Test that nested spans maintain parent/child relationships."""
        with Span("span_1", "test", "outer") as outer:
            with Span("span_2", "test", "inner") as inner:
                pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        # Should have 4 events: start/end for outer, start/end for inner
        self.assertEqual(len(lines), 4)

        events = [TelemetryEvent(**__import__("json").loads(line)) for line in lines]

        # Check parent/child relationship
        inner_start = events[1]  # Second event (after outer start)
        self.assertEqual(inner_start.span_id, "span_2")
        self.assertEqual(inner_start.parent_span_id, "span_1")

    def test_span_context_propagation(self):
        """Test that span propagates context IDs."""
        with Span("span_1", "test", "test_action"):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        start_event = TelemetryEvent(**__import__("json").loads(lines[0]))

        # Should have context IDs
        self.assertEqual(start_event.queue_id, "test_queue")
        self.assertEqual(start_event.trace_id, "trace_123")

    def test_span_with_exception(self):
        """Test that span records exceptions."""
        try:
            with Span("span_1", "test", "test_action"):
                raise ValueError("Test error")
        except ValueError:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        end_event = TelemetryEvent(**__import__("json").loads(lines[1]))
        self.assertFalse(end_event.success)
        self.assertEqual(end_event.reason, "ValueError")


if __name__ == "__main__":
    unittest.main()
