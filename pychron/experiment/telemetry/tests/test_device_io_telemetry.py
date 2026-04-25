"""Tests for device I/O telemetry wrappers."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.device_io import (
    TelemetryDeviceIOContext,
    get_last_device_io_snapshot,
    record_device_io_event,
    telemetry_device_io,
    telemetry_device_io_context,
)
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.span import set_global_recorder


class TestTelemetryDeviceIODecorator(unittest.TestCase):
    """Test @telemetry_device_io decorator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_decorator_records_device_io_event(self):
        """Test that decorator records device I/O event."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            return "result"

        # Create a mock object with the method
        obj = Mock()
        test_func(obj)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)
        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.event_type, "device_io")
        self.assertEqual(event.payload["device"], "test_device")
        self.assertEqual(event.payload["operation"], "test_op")

    def test_decorator_records_duration(self):
        """Test that decorator records operation duration."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            time.sleep(0.05)
            return "result"

        obj = Mock()
        test_func(obj)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # Should be approximately 50ms
        self.assertGreaterEqual(event.payload["duration_ms"], 40)
        self.assertLess(event.payload["duration_ms"], 100)

    def test_decorator_records_success(self):
        """Test that decorator records success for successful operations."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            return "result"

        obj = Mock()
        test_func(obj)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertTrue(event.payload["success"])
        self.assertEqual(event.level, "debug")

    def test_decorator_records_failure_and_error(self):
        """Test that decorator records failure and error message."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            raise ValueError("Test error message")

        obj = Mock()
        try:
            test_func(obj)
        except ValueError:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertFalse(event.payload["success"])
        self.assertIn("Test error message", event.payload["error"])
        self.assertEqual(event.level, "error")

    def test_decorator_propagates_context_ids(self):
        """Test that decorator propagates context IDs."""
        TelemetryContext.set_run_id("run_123")
        TelemetryContext.set_run_uuid("uuid_456")

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            return "result"

        obj = Mock()
        test_func(obj)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.queue_id, "test_queue")
        self.assertEqual(event.trace_id, "trace_123")
        self.assertEqual(event.run_id, "run_123")
        self.assertEqual(event.run_uuid, "uuid_456")

    def test_decorator_extracts_object_name_from_self(self):
        """Test that decorator extracts class name from self argument."""

        class TestDevice:
            @telemetry_device_io("test_device", "test_op", None)
            def operation(self):
                return "result"

        # Create actual recorder and re-apply decorator
        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            return "result"

        obj = Mock()
        obj.__class__.__name__ = "TestDevice"
        test_func(obj)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.component, "test_device_TestDevice")

    def test_decorator_without_recorder_does_not_crash(self):
        """Test that decorator without recorder still executes function."""

        @telemetry_device_io("test_device", "test_op", None)
        def test_func(self):
            return "result"

        obj = Mock()
        result = test_func(obj)
        self.assertEqual(result, "result")

    def test_decorator_returns_function_result(self):
        """Test that decorator returns the wrapped function's result."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            return "expected_result"

        obj = Mock()
        result = test_func(obj)
        self.assertEqual(result, "expected_result")

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @telemetry_device_io("test_device", "test_op", self.recorder)
        def test_func(self):
            """Test function docstring."""
            return "result"

        self.assertEqual(test_func.__name__, "test_func")
        self.assertEqual(test_func.__doc__, "Test function docstring.")


class TestTelemetryDeviceIOContext(unittest.TestCase):
    """Test TelemetryDeviceIOContext context manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def test_context_manager_records_device_io_event(self):
        """Test that context manager records device I/O event."""
        with TelemetryDeviceIOContext("test_device", "test_op", self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)
        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.event_type, "device_io")
        self.assertEqual(event.payload["device"], "test_device")
        self.assertEqual(event.payload["operation"], "test_op")

    def test_context_manager_records_timing(self):
        """Test that context manager records operation timing."""
        with TelemetryDeviceIOContext("test_device", "test_op", self.recorder):
            time.sleep(0.05)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # Should be approximately 50ms
        self.assertGreaterEqual(event.payload["duration_ms"], 40)
        self.assertLess(event.payload["duration_ms"], 100)

    def test_context_manager_records_success(self):
        """Test that context manager records success."""
        with TelemetryDeviceIOContext("test_device", "test_op", self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertTrue(event.payload["success"])
        self.assertEqual(event.level, "debug")

    def test_context_manager_records_exception(self):
        """Test that context manager records exceptions."""
        try:
            with TelemetryDeviceIOContext("test_device", "test_op", self.recorder):
                raise ValueError("Test error")
        except ValueError:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertFalse(event.payload["success"])
        self.assertIn("Test error", event.payload["error"])
        self.assertEqual(event.level, "error")

    def test_context_manager_propagates_context_ids(self):
        """Test that context manager propagates context IDs."""
        TelemetryContext.set_run_id("run_123")
        TelemetryContext.set_run_uuid("uuid_456")

        with TelemetryDeviceIOContext("test_device", "test_op", self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.queue_id, "test_queue")
        self.assertEqual(event.trace_id, "trace_123")
        self.assertEqual(event.run_id, "run_123")
        self.assertEqual(event.run_uuid, "uuid_456")

    def test_context_manager_with_initial_payload(self):
        """Test that context manager includes initial payload."""
        initial_payload = {"valve_name": "valve_01", "target_state": "open"}

        with TelemetryDeviceIOContext(
            "extraction_line", "open_valve", self.recorder, payload=initial_payload
        ):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["valve_name"], "valve_01")
        self.assertEqual(event.payload["target_state"], "open")

    def test_context_manager_set_payload_updates_payload(self):
        """Test that set_payload updates the payload."""
        with TelemetryDeviceIOContext("spectrometer", "intensity_read", self.recorder) as ctx:
            ctx.set_payload("intensity_value", 42.5)
            ctx.set_payload("detector_num", 3)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["intensity_value"], 42.5)
        self.assertEqual(event.payload["detector_num"], 3)

    def test_context_manager_without_recorder_does_not_crash(self):
        """Test that context manager without recorder still works."""
        with TelemetryDeviceIOContext("test_device", "test_op", None):
            pass
        # Should not raise any exception

    def test_context_manager_returns_self(self):
        """Test that context manager returns self on enter."""
        with TelemetryDeviceIOContext("test_device", "test_op", self.recorder) as ctx:
            self.assertIsInstance(ctx, TelemetryDeviceIOContext)


class TestTelemetryDeviceIOFactory(unittest.TestCase):
    """Test telemetry_device_io_context factory function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "test.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)

        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")

    def tearDown(self):
        """Clean up."""
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()

    def test_factory_creates_context_manager(self):
        """Test that factory creates TelemetryDeviceIOContext."""
        ctx = telemetry_device_io_context("test_device", "test_op", self.recorder)
        self.assertIsInstance(ctx, TelemetryDeviceIOContext)

    def test_factory_with_initial_payload(self):
        """Test that factory accepts and passes initial payload."""
        initial_payload = {"key": "value"}
        ctx = telemetry_device_io_context(
            "test_device", "test_op", self.recorder, payload=initial_payload
        )
        self.assertEqual(ctx.payload["key"], "value")

    def test_factory_usage_pattern(self):
        """Test typical factory usage pattern."""
        with telemetry_device_io_context("spectrometer", "intensity_read", self.recorder) as ctx:
            ctx.set_payload("reading", 123.45)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["reading"], 123.45)


class TestDeviceIOTelemetryHelpers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "helpers.jsonl"
        self.recorder = TelemetryRecorder(self.log_path)
        TelemetryContext.clear()
        TelemetryContext.set_queue_id("test_queue")
        TelemetryContext.set_trace_id("trace_123")
        TelemetryContext.set_run_id("run_123")
        TelemetryContext.set_run_uuid("uuid_456")
        set_global_recorder(self.recorder)

    def tearDown(self):
        self.recorder.close()
        self.temp_dir.cleanup()
        TelemetryContext.clear()
        set_global_recorder(None)

    def test_record_device_io_event_uses_global_recorder(self):
        record_device_io_event(
            "spectrometer",
            "ask",
            stage="start",
            payload={"command": "GetData"},
            flush=True,
        )

        with open(self.log_path) as rfile:
            lines = rfile.readlines()

        self.assertEqual(len(lines), 1)
        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["stage"], "start")
        self.assertEqual(event.queue_id, "test_queue")
        self.assertEqual(event.run_id, "run_123")

    def test_get_last_device_io_snapshot_returns_latest_event(self):
        record_device_io_event(
            "spectrometer",
            "read",
            stage="start",
            payload={"command": "ReadData"},
        )

        snapshot = get_last_device_io_snapshot("trace_123", "run_123")

        self.assertIn("spectrometer", snapshot)
        self.assertEqual(snapshot["spectrometer"]["operation"], "read")
        self.assertEqual(snapshot["spectrometer"]["stage"], "start")


if __name__ == "__main__":
    unittest.main()
