"""Tests for HeartbeatTelemetryListener integration with pychron telemetry system."""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import tempfile
import json

from pychron.hardware.core.watchdog.telemetry_integration import HeartbeatTelemetryListener
from pychron.experiment.telemetry.event import TelemetryEvent, EventType


class TestHeartbeatTelemetryListener(unittest.TestCase):
    """Test suite for HeartbeatTelemetryListener."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_recorder = Mock()
        self.listener = HeartbeatTelemetryListener(recorder=self.mock_recorder)

    def test_init_with_recorder(self):
        """Test listener initialization with explicit recorder."""
        listener = HeartbeatTelemetryListener(recorder=self.mock_recorder)
        self.assertEqual(listener.recorder, self.mock_recorder)

    def test_init_without_recorder(self):
        """Test listener initialization without recorder."""
        listener = HeartbeatTelemetryListener()
        self.assertIsNone(listener.recorder)

    def test_get_recorder_with_explicit(self):
        """Test _get_recorder returns explicit recorder."""
        recorder = self.listener._get_recorder()
        self.assertEqual(recorder, self.mock_recorder)

    def test_on_state_change_healthy_to_degraded(self):
        """Test state change event from HEALTHY to DEGRADED."""
        self.listener.on_state_change("MS", "HEALTHY", "DEGRADED")

        # Verify event was recorded
        self.mock_recorder.record_event.assert_called_once()
        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and basic fields
        self.assertEqual(event.event_type, EventType.DEVICE_HEALTH_STATE_CHANGE.value)
        self.assertEqual(event.component, "device_health")
        self.assertEqual(event.action, "state_transition")
        self.assertEqual(event.state_from, "HEALTHY")
        self.assertEqual(event.state_to, "DEGRADED")
        self.assertEqual(event.level, "warning")

        # Check payload
        self.assertEqual(event.payload["device"], "MS")
        self.assertEqual(event.payload["from_state"], "HEALTHY")
        self.assertEqual(event.payload["to_state"], "DEGRADED")

    def test_on_state_change_to_healthy(self):
        """Test state change event returning to HEALTHY."""
        self.listener.on_state_change("pump", "DEGRADED", "HEALTHY")

        event = self.mock_recorder.record_event.call_args[0][0]
        self.assertEqual(event.level, "info")
        self.assertEqual(event.state_to, "HEALTHY")

    def test_on_state_change_unavailable(self):
        """Test state change to UNAVAILABLE."""
        self.listener.on_state_change("detector", "DEGRADED", "UNAVAILABLE")

        event = self.mock_recorder.record_event.call_args[0][0]
        self.assertEqual(event.state_from, "DEGRADED")
        self.assertEqual(event.state_to, "UNAVAILABLE")
        self.assertEqual(event.level, "warning")

    def test_on_failure_basic(self):
        """Test device failure event."""
        self.listener.on_failure("EL", failure_count=2, error="Connection timeout")

        self.mock_recorder.record_event.assert_called_once()
        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and fields
        self.assertEqual(event.event_type, EventType.DEVICE_HEALTH_FAILURE.value)
        self.assertEqual(event.component, "device_health")
        self.assertEqual(event.action, "failure")
        self.assertEqual(event.level, "error")
        self.assertFalse(event.success)
        self.assertEqual(event.error, "Connection timeout")

        # Check payload
        self.assertEqual(event.payload["device"], "EL")
        self.assertEqual(event.payload["failure_count"], 2)
        self.assertEqual(event.payload["error"], "Connection timeout")

    def test_on_failure_without_error_message(self):
        """Test failure event without error message."""
        self.listener.on_failure("MS", failure_count=1)

        event = self.mock_recorder.record_event.call_args[0][0]
        self.assertIsNone(event.error)
        self.assertEqual(event.payload["error"], None)

    def test_on_recovery_attempt(self):
        """Test device recovery attempt event."""
        self.listener.on_recovery_attempt("pump", attempt_count=1)

        self.mock_recorder.record_event.assert_called_once()
        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and fields
        self.assertEqual(event.event_type, EventType.DEVICE_HEALTH_RECOVERY_ATTEMPT.value)
        self.assertEqual(event.component, "device_health")
        self.assertEqual(event.action, "recovery_attempt")
        self.assertEqual(event.level, "warning")

        # Check payload
        self.assertEqual(event.payload["device"], "pump")
        self.assertEqual(event.payload["attempt_count"], 1)

    def test_on_recovery_success(self):
        """Test successful device recovery event."""
        self.listener.on_recovery_success("detector", attempt_count=3)

        self.mock_recorder.record_event.assert_called_once()
        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and fields
        self.assertEqual(event.event_type, EventType.DEVICE_HEALTH_RECOVERY_SUCCESS.value)
        self.assertEqual(event.component, "device_health")
        self.assertEqual(event.action, "recovery_success")
        self.assertEqual(event.level, "info")
        self.assertTrue(event.success)

        # Check payload
        self.assertEqual(event.payload["device"], "detector")
        self.assertEqual(event.payload["recovery_attempts"], 3)

    def test_on_quorum_check_passed(self):
        """Test quorum check event that passed."""
        required = ["MS", "detector"]
        healthy = ["MS", "detector"]
        unhealthy = []

        self.listener.on_quorum_check(
            phase_name="measurement",
            passed=True,
            required_devices=required,
            healthy_devices=healthy,
            unhealthy_devices=unhealthy,
        )

        self.mock_recorder.record_event.assert_called_once()
        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and fields
        self.assertEqual(event.event_type, EventType.DEVICE_QUORUM_CHECK.value)
        self.assertEqual(event.component, "device_health")
        self.assertEqual(event.action, "quorum_check")
        self.assertEqual(event.level, "info")
        self.assertTrue(event.success)

        # Check payload
        self.assertEqual(event.payload["phase"], "measurement")
        self.assertTrue(event.payload["passed"])
        self.assertEqual(event.payload["required_devices"], required)
        self.assertEqual(event.payload["healthy_devices"], healthy)
        self.assertEqual(event.payload["unhealthy_devices"], unhealthy)
        self.assertEqual(event.payload["healthy_count"], 2)
        self.assertEqual(event.payload["unhealthy_count"], 0)

    def test_on_quorum_check_failed(self):
        """Test quorum check event that failed."""
        required = ["MS", "detector", "pump"]
        healthy = ["MS"]
        unhealthy = ["detector", "pump"]

        self.listener.on_quorum_check(
            phase_name="extraction",
            passed=False,
            required_devices=required,
            healthy_devices=healthy,
            unhealthy_devices=unhealthy,
        )

        event = self.mock_recorder.record_event.call_args[0][0]

        # Check event type and fields
        self.assertEqual(event.event_type, EventType.DEVICE_QUORUM_CHECK.value)
        self.assertEqual(event.level, "warning")
        self.assertFalse(event.success)

        # Check payload
        self.assertEqual(event.payload["phase"], "extraction")
        self.assertFalse(event.payload["passed"])
        self.assertEqual(event.payload["healthy_count"], 1)
        self.assertEqual(event.payload["unhealthy_count"], 2)

    def test_no_recorder_state_change(self):
        """Test on_state_change with no recorder does nothing."""
        listener = HeartbeatTelemetryListener(recorder=None)

        # Should not raise an exception
        listener.on_state_change("MS", "HEALTHY", "DEGRADED")

    def test_no_recorder_failure(self):
        """Test on_failure with no recorder does nothing."""
        listener = HeartbeatTelemetryListener(recorder=None)

        # Should not raise an exception
        listener.on_failure("EL", failure_count=2)

    def test_no_recorder_recovery_attempt(self):
        """Test on_recovery_attempt with no recorder does nothing."""
        listener = HeartbeatTelemetryListener(recorder=None)

        # Should not raise an exception
        listener.on_recovery_attempt("pump", attempt_count=1)

    def test_no_recorder_recovery_success(self):
        """Test on_recovery_success with no recorder does nothing."""
        listener = HeartbeatTelemetryListener(recorder=None)

        # Should not raise an exception
        listener.on_recovery_success("detector", attempt_count=3)

    def test_no_recorder_quorum_check(self):
        """Test on_quorum_check with no recorder does nothing."""
        listener = HeartbeatTelemetryListener(recorder=None)

        # Should not raise an exception
        listener.on_quorum_check(
            phase_name="measurement",
            passed=True,
            required_devices=["MS"],
            healthy_devices=["MS"],
            unhealthy_devices=[],
        )

    def test_multiple_events_in_sequence(self):
        """Test multiple events recorded in sequence."""
        self.listener.on_state_change("MS", "HEALTHY", "DEGRADED")
        self.listener.on_failure("MS", failure_count=2, error="Timeout")
        self.listener.on_recovery_attempt("MS", attempt_count=1)
        self.listener.on_recovery_success("MS", attempt_count=1)

        # Verify 4 events were recorded
        self.assertEqual(self.mock_recorder.record_event.call_count, 4)

        # Verify event order and types
        calls = self.mock_recorder.record_event.call_args_list
        event_types = [call[0][0].event_type for call in calls]

        self.assertEqual(
            event_types,
            [
                EventType.DEVICE_HEALTH_STATE_CHANGE.value,
                EventType.DEVICE_HEALTH_FAILURE.value,
                EventType.DEVICE_HEALTH_RECOVERY_ATTEMPT.value,
                EventType.DEVICE_HEALTH_RECOVERY_SUCCESS.value,
            ],
        )

    def test_event_timestamps(self):
        """Test that events have timestamps."""
        self.listener.on_state_change("MS", "HEALTHY", "DEGRADED")
        event = self.mock_recorder.record_event.call_args[0][0]

        # Event should have a ts field
        self.assertIsNotNone(event.ts)
        self.assertIsInstance(event.ts, float)
        self.assertGreater(event.ts, 0)

    def test_multiple_devices_events(self):
        """Test events for multiple devices."""
        self.listener.on_state_change("MS", "HEALTHY", "DEGRADED")
        self.listener.on_state_change("pump", "HEALTHY", "DEGRADED")
        self.listener.on_state_change("detector", "HEALTHY", "DEGRADED")

        self.assertEqual(self.mock_recorder.record_event.call_count, 3)

        # Verify devices in payloads
        calls = self.mock_recorder.record_event.call_args_list
        devices = [call[0][0].payload["device"] for call in calls]

        self.assertEqual(devices, ["MS", "pump", "detector"])

    @patch("pychron.hardware.core.watchdog.telemetry_integration.TelemetryContext")
    def test_state_change_with_context(self, mock_context):
        """Test state change event includes telemetry context."""
        mock_context.get_queue_id.return_value = "queue_001"
        mock_context.get_run_id.return_value = "sample_001_00_00"
        mock_context.get_run_uuid.return_value = "uuid-123"
        mock_context.get_trace_id.return_value = "trace-456"
        mock_context.get_current_span_id.return_value = "span-789"

        self.listener.on_state_change("MS", "HEALTHY", "DEGRADED")

        event = self.mock_recorder.record_event.call_args[0][0]

        self.assertEqual(event.queue_id, "queue_001")
        self.assertEqual(event.run_id, "sample_001_00_00")
        self.assertEqual(event.run_uuid, "uuid-123")
        self.assertEqual(event.trace_id, "trace-456")
        self.assertEqual(event.parent_span_id, "span-789")

    def test_quorum_check_partial_healthy(self):
        """Test quorum check with partial device health."""
        self.listener.on_quorum_check(
            phase_name="save",
            passed=True,
            required_devices=["database", "dvc"],
            healthy_devices=["database"],
            unhealthy_devices=["dvc"],
        )

        event = self.mock_recorder.record_event.call_args[0][0]

        self.assertTrue(event.success)
        self.assertEqual(event.payload["healthy_count"], 1)
        self.assertEqual(event.payload["unhealthy_count"], 1)

    def test_event_payload_structure(self):
        """Test that event payloads have correct structure."""
        self.listener.on_failure("MS", failure_count=3, error="Test error")

        event = self.mock_recorder.record_event.call_args[0][0]

        # Verify payload is a dict with expected keys
        self.assertIsInstance(event.payload, dict)
        self.assertIn("device", event.payload)
        self.assertIn("failure_count", event.payload)
        self.assertIn("error", event.payload)


if __name__ == "__main__":
    unittest.main()
