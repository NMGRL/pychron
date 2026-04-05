"""Tests for monitor and interlock telemetry wrappers."""

import json
import tempfile
import time
import unittest
from pathlib import Path

from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.monitor_interlock import (
    TelemetryInterlockEvaluation,
    TelemetryMonitorDecision,
    telemetry_interlock_evaluation,
    telemetry_monitor_decision,
)
from pychron.experiment.telemetry.recorder import TelemetryRecorder


class TestTelemetryMonitorDecision(unittest.TestCase):
    """Test TelemetryMonitorDecision context manager."""

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

    def test_monitor_decision_records_event(self):
        """Test that monitor decision records MONITOR_CHECK event."""
        with TelemetryMonitorDecision(
            "pressure_monitor", "pressure_high", {"current_pressure": 50.5}, self.recorder
        ):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)
        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.event_type, "monitor_check")
        self.assertEqual(event.component, "pressure_monitor")
        self.assertEqual(event.action, "pressure_high")

    def test_monitor_decision_includes_context_data(self):
        """Test that monitor decision includes context data in payload."""
        context_data = {"current_pressure": 50.5, "threshold": 50.0}

        with TelemetryMonitorDecision(
            "pressure_monitor", "pressure_high", context_data, self.recorder
        ):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["current_pressure"], 50.5)
        self.assertEqual(event.payload["threshold"], 50.0)

    def test_monitor_decision_records_timing(self):
        """Test that monitor decision records timing."""
        with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, self.recorder):
            time.sleep(0.05)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # Should be approximately 50ms
        self.assertGreaterEqual(event.payload["duration_ms"], 40)
        self.assertLess(event.payload["duration_ms"], 100)

    def test_monitor_decision_record_action_success(self):
        """Test that record_action captures successful action."""
        with TelemetryMonitorDecision(
            "pressure_monitor", "pressure_high", {}, self.recorder
        ) as monitor:
            monitor.record_action("pause_run", success=True)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["action"], "pause_run")
        self.assertTrue(event.payload["action_success"])

    def test_monitor_decision_record_action_failure(self):
        """Test that record_action captures failed action."""
        with TelemetryMonitorDecision(
            "pressure_monitor", "pressure_high", {}, self.recorder
        ) as monitor:
            monitor.record_action("skip_run", success=False)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["action"], "skip_run")
        self.assertFalse(event.payload["action_success"])

    def test_monitor_decision_level_info_without_exception(self):
        """Test that level is 'info' when no exception occurs."""
        with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.level, "info")

    def test_monitor_decision_level_warning_with_exception(self):
        """Test that level is 'warning' when exception occurs."""
        try:
            with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, self.recorder):
                raise RuntimeError("Monitor action failed")
        except RuntimeError:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.level, "warning")

    def test_monitor_decision_propagates_context_ids(self):
        """Test that monitor decision propagates context IDs."""
        TelemetryContext.set_run_id("run_123")
        TelemetryContext.set_run_uuid("uuid_456")

        with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.queue_id, "test_queue")
        self.assertEqual(event.trace_id, "trace_123")
        self.assertEqual(event.run_id, "run_123")
        self.assertEqual(event.run_uuid, "uuid_456")

    def test_monitor_decision_without_recorder_does_not_crash(self):
        """Test that monitor decision without recorder still works."""
        with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, None) as monitor:
            monitor.record_action("pause_run", success=True)
        # Should not raise any exception

    def test_monitor_decision_without_action_recorded(self):
        """Test that monitor decision works without action recorded."""
        with TelemetryMonitorDecision("pressure_monitor", "pressure_high", {}, self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # action should not be in payload if not recorded
        self.assertNotIn("action", event.payload)

    def test_monitor_decision_returns_self(self):
        """Test that monitor decision returns self on enter."""
        with TelemetryMonitorDecision(
            "pressure_monitor", "pressure_high", {}, self.recorder
        ) as monitor:
            self.assertIsInstance(monitor, TelemetryMonitorDecision)


class TestTelemetryInterlockEvaluation(unittest.TestCase):
    """Test TelemetryInterlockEvaluation context manager."""

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

    def test_interlock_evaluation_records_event(self):
        """Test that interlock evaluation records INTERLOCK_CHECK event."""
        with TelemetryInterlockEvaluation(
            "sample_weight_check",
            {"sample_weight_min": 5.0, "sample_weight_max": 100.0},
            self.recorder,
        ):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)
        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.event_type, "interlock_check")
        self.assertEqual(event.action, "sample_weight_check")

    def test_interlock_evaluation_includes_context_data(self):
        """Test that interlock evaluation includes context data."""
        context_data = {"sample_weight_min": 5.0, "sample_weight_max": 100.0}

        with TelemetryInterlockEvaluation("sample_weight_check", context_data, self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["sample_weight_min"], 5.0)
        self.assertEqual(event.payload["sample_weight_max"], 100.0)

    def test_interlock_evaluation_records_timing(self):
        """Test that interlock evaluation records timing."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder):
            time.sleep(0.05)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # Should be approximately 50ms
        self.assertGreaterEqual(event.payload["duration_ms"], 40)
        self.assertLess(event.payload["duration_ms"], 100)

    def test_interlock_evaluation_set_result_pass(self):
        """Test that set_result records passing result."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder) as interlock:
            interlock.set_result(True, {"actual_weight": 50.0})

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertTrue(event.payload["passes"])
        self.assertEqual(event.payload["actual_weight"], 50.0)

    def test_interlock_evaluation_set_result_fail(self):
        """Test that set_result records failing result."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder) as interlock:
            interlock.set_result(False, {"actual_weight": 2.0})

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertFalse(event.payload["passes"])
        self.assertEqual(event.payload["actual_weight"], 2.0)

    def test_interlock_evaluation_level_info_when_passes(self):
        """Test that level is 'info' when interlock passes."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder) as interlock:
            interlock.set_result(True)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.level, "info")

    def test_interlock_evaluation_level_warning_when_fails(self):
        """Test that level is 'warning' when interlock fails."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder) as interlock:
            interlock.set_result(False)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.level, "warning")

    def test_interlock_evaluation_level_info_when_exception_occurs(self):
        """Test that level is 'info' when no result set (no exception)."""
        try:
            with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder):
                pass
        except Exception:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.level, "info")

    def test_interlock_evaluation_passes_defaults_to_no_exception(self):
        """Test that passes defaults to no exception when result not set."""
        try:
            with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder):
                pass
        except Exception:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        # Since no exception occurred, passes should be True
        self.assertTrue(event.payload["passes"])

    def test_interlock_evaluation_passes_reflects_exception(self):
        """Test that passes is False when exception occurs."""
        try:
            with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder):
                raise ValueError("Evaluation error")
        except ValueError:
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertFalse(event.payload["passes"])
        self.assertIn("Evaluation error", event.payload["error"])

    def test_interlock_evaluation_propagates_context_ids(self):
        """Test that interlock evaluation propagates context IDs."""
        TelemetryContext.set_run_id("run_123")
        TelemetryContext.set_run_uuid("uuid_456")

        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder):
            pass

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.queue_id, "test_queue")
        self.assertEqual(event.trace_id, "trace_123")
        self.assertEqual(event.run_id, "run_123")
        self.assertEqual(event.run_uuid, "uuid_456")

    def test_interlock_evaluation_without_recorder_does_not_crash(self):
        """Test that interlock evaluation without recorder still works."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, None) as interlock:
            interlock.set_result(True)
        # Should not raise any exception

    def test_interlock_evaluation_returns_self(self):
        """Test that interlock evaluation returns self on enter."""
        with TelemetryInterlockEvaluation("sample_weight_check", {}, self.recorder) as interlock:
            self.assertIsInstance(interlock, TelemetryInterlockEvaluation)


class TestTelemetryMonitorDecisionFactory(unittest.TestCase):
    """Test telemetry_monitor_decision factory function."""

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

    def test_factory_creates_monitor_decision(self):
        """Test that factory creates TelemetryMonitorDecision."""
        ctx = telemetry_monitor_decision("pressure_monitor", "pressure_high", {}, self.recorder)
        self.assertIsInstance(ctx, TelemetryMonitorDecision)

    def test_factory_usage_pattern(self):
        """Test typical factory usage pattern."""
        with telemetry_monitor_decision(
            "pressure_monitor",
            "pressure_high",
            {"current_pressure": 50.5},
            self.recorder,
        ) as monitor:
            monitor.record_action("pause_run", success=True)

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertEqual(event.payload["action"], "pause_run")


class TestTelemetryInterlockEvaluationFactory(unittest.TestCase):
    """Test telemetry_interlock_evaluation factory function."""

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

    def test_factory_creates_interlock_evaluation(self):
        """Test that factory creates TelemetryInterlockEvaluation."""
        ctx = telemetry_interlock_evaluation("sample_weight_check", {}, self.recorder)
        self.assertIsInstance(ctx, TelemetryInterlockEvaluation)

    def test_factory_usage_pattern(self):
        """Test typical factory usage pattern."""
        with telemetry_interlock_evaluation(
            "sample_weight_check",
            {"sample_weight_min": 5.0, "sample_weight_max": 100.0},
            self.recorder,
        ) as interlock:
            interlock.set_result(True, {"actual_weight": 50.0})

        self.recorder.flush()

        with open(self.log_path) as f:
            lines = f.readlines()

        event = TelemetryEvent(**json.loads(lines[0]))
        self.assertTrue(event.payload["passes"])


if __name__ == "__main__":
    unittest.main()
