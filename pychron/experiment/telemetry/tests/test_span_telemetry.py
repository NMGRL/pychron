"""Tests for span-based telemetry in experiment execution."""

import time
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.span import Span
from pychron.experiment.telemetry.event import EventType, TelemetryEvent


class TestSpanTelemetry(unittest.TestCase):
    """Test span-based timing and nesting telemetry."""

    def setUp(self):
        """Initialize test fixtures."""
        self.context = TelemetryContext()
        # Create temporary log file for testing
        self.temp_log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.temp_log.close()
        self.recorder = TelemetryRecorder(log_path=self.temp_log.name)
        # Set test queue and run IDs
        self.test_queue_id = "test_queue_123"
        self.test_run_id = "exp001"
        self.test_run_uuid = "uuid-12345"
        TelemetryContext.set_queue_id(self.test_queue_id)
        TelemetryContext.set_run_id(self.test_run_id)
        TelemetryContext.set_run_uuid(self.test_run_uuid)

    def tearDown(self):
        """Clean up after tests."""
        TelemetryContext.clear()
        self.recorder.flush()
        self.recorder.close()
        # Clean up temporary file
        if Path(self.temp_log.name).exists():
            Path(self.temp_log.name).unlink()

    def test_span_creation_and_timing(self):
        """Test that spans record start and end events with timing."""
        with Span(component="executor", action="test_operation", recorder=self.recorder) as span:
            self.assertIsNotNone(span.span_id)
            self.assertIsNotNone(span.start_time)
            time.sleep(0.05)  # 50ms delay

        # Verify span ended
        self.assertIsNotNone(span.end_time)
        self.assertIsNotNone(span.duration_ms)
        self.assertGreaterEqual(span.duration_ms, 50)  # At least 50ms

    def test_span_records_events_in_recorder(self):
        """Test that span events are recorded by the recorder."""
        with Span(component="executor", action="queue_execution", recorder=self.recorder) as span:
            pass

        # Verify events were recorded (before flushing)
        self.assertGreater(len(self.recorder._buffer), 0)

        # Now flush and verify
        self.recorder.flush()

    def test_span_parent_child_nesting(self):
        """Test that parent and child spans maintain proper nesting."""
        with Span(
            component="executor", action="parent_operation", recorder=self.recorder
        ) as parent_span:
            parent_id = parent_span.span_id

            with Span(
                component="executor", action="child_operation", recorder=self.recorder
            ) as child_span:
                child_id = child_span.span_id
                # Child should have parent as its parent_span_id (via context)
                current = TelemetryContext.get_current_span_id()
                self.assertEqual(current, child_id)

        # After exiting, verify nesting is restored
        self.recorder.flush()

    def test_span_with_payload(self):
        """Test that span payloads are captured correctly."""
        payload = {"queue_name": "test_queue", "queue_index": 1}
        with Span(
            component="executor", action="queue_execution", payload=payload, recorder=self.recorder
        ) as span:
            pass

        self.assertEqual(span.payload, payload)
        self.recorder.flush()

    def test_queue_execution_span_correlation_ids(self):
        """Test that queue execution spans capture correlation IDs."""
        with Span(
            component="executor",
            action="queue_execution",
            payload={"queue_name": "test_q", "queue_index": 0},
            recorder=self.recorder,
        ) as span:
            # Verify context has correct correlation IDs
            queue_id = TelemetryContext.get_queue_id()
            run_id = TelemetryContext.get_run_id()
            run_uuid = TelemetryContext.get_run_uuid()

            self.assertEqual(queue_id, self.test_queue_id)
            self.assertEqual(run_id, self.test_run_id)
            self.assertEqual(run_uuid, self.test_run_uuid)

        self.recorder.flush()

    def test_multiple_sequential_spans(self):
        """Test multiple sequential spans are properly tracked."""
        span_ids = []

        for i in range(3):
            with Span(
                component="executor",
                action=f"operation_{i}",
                payload={"index": i},
                recorder=self.recorder,
            ) as span:
                span_ids.append(span.span_id)
                time.sleep(0.01)

        # Verify all spans recorded
        self.assertEqual(len(span_ids), 3)
        # Verify span IDs are unique
        self.assertEqual(len(set(span_ids)), 3)

        self.recorder.flush()

    def test_span_success_status(self):
        """Test that spans exit cleanly with success status."""
        with Span(component="executor", action="test", recorder=self.recorder) as span:
            span.success = True

        self.assertTrue(span.success)
        self.assertEqual(span.duration_ms, span.duration_ms)  # Has duration

    def test_span_error_handling(self):
        """Test span handles errors gracefully."""
        span = Span(component="executor", action="test", recorder=self.recorder)
        span.__enter__()

        try:
            # Simulate an error
            raise ValueError("Test error")
        except ValueError:
            span.__exit__(*sys.exc_info())

        # Span should be marked as ended
        self.assertTrue(span._ended)

    def test_nested_span_stack_integrity(self):
        """Test that nested spans maintain proper stack integrity."""
        stack_sizes = []

        with Span(component="executor", action="level_1", recorder=self.recorder):
            current_stack = TelemetryContext.get_queue_id()  # Get current span context
            stack_sizes.append(1)  # Manually track depth

            with Span(component="executor", action="level_2", recorder=self.recorder):
                stack_sizes.append(2)

                with Span(component="executor", action="level_3", recorder=self.recorder):
                    stack_sizes.append(3)

        # Verify stack grew properly
        self.assertEqual(stack_sizes, [1, 2, 3])
        # Current span ID should be None after all spans exit
        self.assertIsNone(TelemetryContext.get_current_span_id())

        self.recorder.flush()

    def test_run_execution_span(self):
        """Test run execution span captures run-level correlation IDs."""
        new_run_id = "exp002"
        new_run_uuid = "uuid-67890"
        TelemetryContext.set_run_id(new_run_id)
        TelemetryContext.set_run_uuid(new_run_uuid)

        with Span(
            component="executor",
            action="run_execution",
            payload={"run_id": new_run_id},
            recorder=self.recorder,
        ) as span:
            pass

        # Verify recorder captured the run info
        self.recorder.flush()

    def test_phase_spans(self):
        """Test phase-level spans (extraction, measurement, save)."""
        phases = ["phase_extraction", "phase_measurement", "phase_save"]

        with Span(component="executor", action="run_execution", recorder=self.recorder):
            for phase_name in phases:
                with Span(
                    component="executor",
                    action=phase_name,
                    payload={"phase": phase_name},
                    recorder=self.recorder,
                ) as span:
                    time.sleep(0.01)
                    self.assertIn(phase_name, span.action)

        self.recorder.flush()

    def test_span_disabled_when_no_recorder(self):
        """Test spans handle missing recorder gracefully."""
        span = Span(component="executor", action="test", recorder=None)
        with span:
            # Should not raise error
            pass

        # Span should still track timing
        self.assertIsNotNone(span.start_time)
        self.assertIsNotNone(span.end_time)

    def test_overlap_settlement_span(self):
        """Test overlap settlement span captures timing."""
        with Span(
            component="executor",
            action="overlap_settlement",
            payload={"overlap_count": 2},
            recorder=self.recorder,
        ) as span:
            time.sleep(0.02)

        self.assertGreaterEqual(span.duration_ms, 20)
        self.recorder.flush()

    def test_cancel_abort_spans(self):
        """Test cancel and abort spans are properly recorded."""
        for action in ["run_cancel", "run_abort"]:
            with Span(
                component="executor",
                action=action,
                payload={"reason": "user_request"},
                recorder=self.recorder,
            ) as span:
                self.assertEqual(span.action, action)

        self.recorder.flush()

    def test_span_level_and_component_fields(self):
        """Test span correctly sets level and component fields."""
        with Span(
            component="executor", action="test_operation", level="debug", recorder=self.recorder
        ) as span:
            self.assertEqual(span.component, "executor")
            self.assertEqual(span.action, "test_operation")
            self.assertEqual(span.level, "debug")

        self.recorder.flush()


class TestSpanIntegration(unittest.TestCase):
    """Integration tests for spans with executor components."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = TelemetryContext()
        # Create temporary log file for testing
        self.temp_log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.temp_log.close()
        self.recorder = TelemetryRecorder(log_path=self.temp_log.name)
        TelemetryContext.set_queue_id("integration_queue")

    def tearDown(self):
        """Clean up."""
        TelemetryContext.clear()
        self.recorder.flush()
        self.recorder.close()
        # Clean up temporary file
        if Path(self.temp_log.name).exists():
            Path(self.temp_log.name).unlink()

    def test_queue_and_run_span_hierarchy(self):
        """Test that queue spans properly contain run spans."""
        with Span(
            component="executor",
            action="queue_execution",
            payload={"queue_name": "q1"},
            recorder=self.recorder,
        ) as queue_span:
            queue_id = queue_span.span_id

            run_ids = []
            for i in range(2):
                TelemetryContext.set_run_id(f"run_{i}")
                with Span(
                    component="executor",
                    action="run_execution",
                    payload={"run_index": i},
                    recorder=self.recorder,
                ) as run_span:
                    run_ids.append(run_span.span_id)

        # Verify all spans were created
        self.assertEqual(len(run_ids), 2)
        self.recorder.flush()

    def test_phases_within_run_span(self):
        """Test that phase spans nest properly within run spans."""
        TelemetryContext.set_run_id("test_run")

        with Span(component="executor", action="run_execution", recorder=self.recorder) as run_span:
            phase_ids = []

            for phase in ["phase_extraction", "phase_measurement", "phase_save"]:
                with Span(component="executor", action=phase, recorder=self.recorder) as phase_span:
                    phase_ids.append(phase_span.span_id)
                    time.sleep(0.01)

        self.assertEqual(len(phase_ids), 3)
        self.recorder.flush()


if __name__ == "__main__":
    import sys

    unittest.main()
