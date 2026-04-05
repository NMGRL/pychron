"""Tests for Phase 5 executor integration telemetry."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.event import TelemetryEvent, EventType
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.span import Span, set_global_recorder
from pychron.experiment.state_machines.controller import ExecutorController


class TestExecutorTelemetryInitialization(unittest.TestCase):
    """Test executor-level telemetry initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"

        # Mock executor
        self.mock_executor = Mock()
        self.controller = ExecutorController(self.mock_executor)

    def tearDown(self):
        """Clean up."""
        if self.controller.telemetry_recorder:
            self.controller.telemetry_recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def test_controller_initializes_telemetry_when_enabled(self):
        """Test that controller initializes telemetry infrastructure."""
        with patch("pychron.experiment.state_machines.controller.globalv") as mock_globalv:
            mock_globalv.telemetry_enabled = True
            controller = ExecutorController(self.mock_executor)

            self.assertIsNotNone(controller.telemetry_context)
            self.assertIsNotNone(controller.telemetry_recorder)

    def test_controller_telemetry_disabled_by_default(self):
        """Test that controller has telemetry disabled by default."""
        with patch("pychron.experiment.state_machines.controller.globalv") as mock_globalv:
            mock_globalv.telemetry_enabled = False
            controller = ExecutorController(self.mock_executor)

            self.assertIsNone(controller.telemetry_context)
            self.assertIsNone(controller.telemetry_recorder)

    def test_controller_registers_state_machine_listener(self):
        """Test that controller registers listener for state machine events."""
        with patch("pychron.experiment.state_machines.controller.globalv") as mock_globalv:
            mock_globalv.telemetry_enabled = True
            controller = ExecutorController(self.mock_executor)

            # Should have registered at least one callback
            self.assertGreater(len(controller._on_transition), 0)


class TestQueueLevelTelemetryContext(unittest.TestCase):
    """Test queue-level telemetry context setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        set_global_recorder(self.recorder)

        TelemetryContext.clear()

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_queue_context_propagation(self):
        """Test that queue context is properly set and propagated."""
        queue_name = "test_queue_001"
        trace_id = f"queue_{queue_name}_{int(time.time())}"

        TelemetryContext.set_queue_id(queue_name)
        TelemetryContext.set_trace_id(trace_id)

        # Verify context is accessible
        self.assertEqual(TelemetryContext.get_queue_id(), queue_name)
        self.assertEqual(TelemetryContext.get_trace_id(), trace_id)

    def test_queue_span_captures_correlation_ids(self):
        """Test that queue execution span captures queue correlation IDs."""
        queue_name = "test_queue_001"
        trace_id = f"queue_{queue_name}_{int(time.time())}"

        TelemetryContext.set_queue_id(queue_name)
        TelemetryContext.set_trace_id(trace_id)

        with Span(trace_id, "queue_executor", "queue_execution", recorder=self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        # Should have start and end span events
        self.assertEqual(len(lines), 2)

        start_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(start_event.queue_id, queue_name)
        self.assertEqual(start_event.trace_id, trace_id)


class TestRunLevelTelemetryContext(unittest.TestCase):
    """Test run-level telemetry context setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
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

    def test_run_context_propagation(self):
        """Test that run context is properly set and propagated."""
        run_id = "sample-001-00-00"
        run_uuid = "550e8400-e29b-41d4-a716-446655440000"

        TelemetryContext.set_run_id(run_id)
        TelemetryContext.set_run_uuid(run_uuid)

        # Verify context is accessible
        self.assertEqual(TelemetryContext.get_run_id(), run_id)
        self.assertEqual(TelemetryContext.get_run_uuid(), run_uuid)

    def test_run_span_captures_correlation_ids(self):
        """Test that run execution span captures run correlation IDs."""
        run_id = "sample-001-00-00"
        run_uuid = "550e8400-e29b-41d4-a716-446655440000"
        span_id = f"run_execution_{run_id}"

        TelemetryContext.set_run_id(run_id)
        TelemetryContext.set_run_uuid(run_uuid)

        with Span(span_id, "run_executor", "run_execution", recorder=self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        start_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(start_event.run_id, run_id)
        self.assertEqual(start_event.run_uuid, run_uuid)
        self.assertEqual(start_event.queue_id, "test_queue")


class TestPhaseSpanIntegration(unittest.TestCase):
    """Test phase-level span integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        set_global_recorder(self.recorder)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")
        TelemetryContext.set_run_id("sample-001-00-00")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_extraction_phase_span(self):
        """Test extraction phase span captures phase context."""
        with Span("extraction_span", "run_executor", "extraction", recorder=self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        # Start and end events
        self.assertEqual(len(lines), 2)

        start_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(start_event.action, "extraction")
        self.assertEqual(start_event.span_id, "extraction_span")

    def test_measurement_phase_span(self):
        """Test measurement phase span captures phase context."""
        with Span("measurement_span", "run_executor", "measurement", recorder=self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        start_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(start_event.action, "measurement")

    def test_save_phase_span(self):
        """Test save phase span captures phase context."""
        with Span("save_span", "run_executor", "save", recorder=self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        start_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(start_event.action, "save")

    def test_phase_span_nesting(self):
        """Test that phase spans nest properly within run span."""
        with Span("run_span", "run_executor", "run", recorder=self.recorder):
            with Span("extraction_span", "run_executor", "extraction", recorder=self.recorder):
                pass
            with Span("measurement_span", "run_executor", "measurement", recorder=self.recorder):
                pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        # 2 events per span * 3 spans = 6 events
        self.assertEqual(len(lines), 6)

        events = [TelemetryEvent(**json.loads(line)) for line in lines]

        # Check parent/child relationships
        run_start = events[0]
        extraction_start = events[1]
        extraction_end = events[2]
        measurement_start = events[3]

        self.assertEqual(extraction_start.parent_span_id, run_start.span_id)
        self.assertEqual(extraction_end.parent_span_id, run_start.span_id)
        self.assertEqual(measurement_start.parent_span_id, run_start.span_id)


class TestTelemetrySessionLifecycle(unittest.TestCase):
    """Test telemetry session lifecycle events."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)

        TelemetryContext.clear()

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def test_telemetry_session_start_event(self):
        """Test recording telemetry session start event."""
        event = TelemetryEvent(
            event_type=EventType.TELEMETRY_SESSION_START.value,
            ts=time.time(),
            level="info",
            component="executor",
            action="session_start",
            payload={"session_id": "session_001"},
        )

        self.recorder.record_event(event)
        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        recorded_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(recorded_event.event_type, "telemetry_session_start")
        self.assertEqual(recorded_event.payload["session_id"], "session_001")

    def test_telemetry_session_end_event(self):
        """Test recording telemetry session end event."""
        event = TelemetryEvent(
            event_type=EventType.TELEMETRY_SESSION_END.value,
            ts=time.time(),
            level="info",
            component="executor",
            action="session_end",
            payload={"session_id": "session_001", "total_queues": 1, "total_runs": 10},
        )

        self.recorder.record_event(event)
        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        recorded_event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(recorded_event.event_type, "telemetry_session_end")
        self.assertEqual(recorded_event.payload["total_runs"], 10)


if __name__ == "__main__":
    unittest.main()
