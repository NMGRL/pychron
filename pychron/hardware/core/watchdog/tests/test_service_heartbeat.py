"""Tests for ServiceHeartbeat and ServiceQuorumChecker."""

import unittest
from unittest.mock import Mock, call, patch
import time

from pychron.hardware.core.watchdog.service_heartbeat import (
    ServiceHeartbeat,
    ServiceState,
)
from pychron.hardware.core.watchdog.service_quorum_checker import (
    ServiceQuorumChecker,
    ServiceQuorumStrategy,
)


class TestServiceHeartbeat(unittest.TestCase):
    """Tests for ServiceHeartbeat state machine."""

    def setUp(self):
        """Set up test fixtures."""
        self.heartbeat = ServiceHeartbeat(
            "TestService",
            is_required=True,
            soft_failure_threshold=2,
            hard_failure_threshold=3,
        )

    def test_init_default_state(self):
        """Test initial state is HEALTHY."""
        self.assertEqual(self.heartbeat.get_state(), ServiceState.HEALTHY)
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertFalse(self.heartbeat.is_degraded())
        self.assertFalse(self.heartbeat.is_unavailable())

    def test_init_parameters(self):
        """Test initialization parameters."""
        hb = ServiceHeartbeat(
            "DVC",
            is_required=True,
            soft_failure_threshold=5,
            hard_failure_threshold=7,
            response_time_threshold=0.5,
        )
        self.assertEqual(hb.service_name, "DVC")
        self.assertTrue(hb.is_required)
        self.assertEqual(hb.soft_failure_threshold, 5)
        self.assertEqual(hb.hard_failure_threshold, 7)
        self.assertEqual(hb.response_time_threshold, 0.5)

    def test_record_success_from_healthy(self):
        """Test success record when healthy."""
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())

    def test_record_success_clears_soft_failures(self):
        """Test success resets soft failure count."""
        self.heartbeat.record_soft_failure()
        self.heartbeat.record_soft_failure()
        self.assertEqual(self.heartbeat._soft_failures, 2)

        self.heartbeat.record_success()
        self.assertEqual(self.heartbeat._soft_failures, 0)

    def test_record_success_with_response_time(self):
        """Test success recording with response time."""
        self.heartbeat.record_success(response_time=0.123)
        stats = self.heartbeat.get_stats()
        self.assertAlmostEqual(stats["avg_response_time"], 0.123, places=3)

    def test_record_soft_failure_increments_count(self):
        """Test soft failure increments counter."""
        self.heartbeat.record_soft_failure("Timeout")
        self.assertEqual(self.heartbeat._soft_failures, 1)

        self.heartbeat.record_soft_failure("Timeout")
        self.assertEqual(self.heartbeat._soft_failures, 2)

    def test_soft_failures_transition_to_degraded(self):
        """Test soft failures transition from HEALTHY to DEGRADED."""
        self.assertEqual(self.heartbeat.get_state(), ServiceState.HEALTHY)

        self.heartbeat.record_soft_failure()
        self.assertEqual(self.heartbeat.get_state(), ServiceState.HEALTHY)

        self.heartbeat.record_soft_failure()
        self.assertEqual(self.heartbeat.get_state(), ServiceState.DEGRADED)
        self.assertTrue(self.heartbeat.is_degraded())

    def test_hard_failures_transition_to_unavailable(self):
        """Test hard failures transition from HEALTHY to UNAVAILABLE."""
        self.heartbeat.record_hard_failure("Connection refused")
        self.assertEqual(self.heartbeat.get_state(), ServiceState.HEALTHY)

        self.heartbeat.record_hard_failure("Connection refused")
        self.assertEqual(self.heartbeat.get_state(), ServiceState.HEALTHY)

        self.heartbeat.record_hard_failure("Connection refused")
        self.assertEqual(self.heartbeat.get_state(), ServiceState.UNAVAILABLE)
        self.assertTrue(self.heartbeat.is_unavailable())

    def test_hard_failure_resets_soft_failures(self):
        """Test hard failure resets soft failure count."""
        self.heartbeat.record_soft_failure()
        self.heartbeat.record_soft_failure()
        self.assertEqual(self.heartbeat._soft_failures, 2)

        self.heartbeat.record_hard_failure()
        self.assertEqual(self.heartbeat._soft_failures, 0)
        self.assertEqual(self.heartbeat._hard_failures, 1)

    def test_recovery_attempt_transitions_to_recovering(self):
        """Test recovery attempt transitions to RECOVERING."""
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.assertTrue(self.heartbeat.is_unavailable())

        self.heartbeat.record_recovery_attempt()
        self.assertEqual(self.heartbeat.get_state(), ServiceState.RECOVERING)
        self.assertTrue(self.heartbeat.is_recovering())

    def test_recovery_success_resets_state(self):
        """Test successful recovery resets all counters."""
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_recovery_attempt()

        self.heartbeat.record_recovery_success()

        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat._soft_failures, 0)
        self.assertEqual(self.heartbeat._hard_failures, 0)
        self.assertEqual(self.heartbeat._recovery_attempts, 0)

    def test_recovery_attempt_throttling(self):
        """Test recovery attempts are throttled."""
        hb = ServiceHeartbeat("test", recovery_check_interval=0.1)
        hb.record_hard_failure()
        hb.record_hard_failure()
        hb.record_hard_failure()

        hb.record_recovery_attempt()
        self.assertEqual(hb._recovery_attempts, 1)

        # Immediate second attempt should be throttled
        hb.record_recovery_attempt()
        self.assertEqual(hb._recovery_attempts, 1)

        # Wait and try again
        time.sleep(0.15)
        hb.record_recovery_attempt()
        self.assertEqual(hb._recovery_attempts, 2)

    def test_time_in_state(self):
        """Test time_in_state tracking."""
        initial_time = self.heartbeat.time_in_state()
        self.assertGreaterEqual(initial_time, 0)

        time.sleep(0.1)
        elapsed = self.heartbeat.time_in_state()
        self.assertGreater(elapsed, 0.05)

    def test_time_since_success(self):
        """Test time_since_success tracking."""
        self.heartbeat.record_success()
        time.sleep(0.05)
        elapsed = self.heartbeat.time_since_success()
        self.assertGreater(elapsed, 0.04)

    def test_state_change_callback(self):
        """Test state change callback is called."""
        callback = Mock()
        self.heartbeat.on_state_change(callback)

        self.heartbeat.record_soft_failure()
        self.heartbeat.record_soft_failure()

        callback.assert_called_once_with("HEALTHY", "DEGRADED")

    def test_failure_callback(self):
        """Test failure callback is called."""
        callback = Mock()
        self.heartbeat.on_failure(callback)

        self.heartbeat.record_soft_failure("Test error")
        callback.assert_called_once_with(1, "Test error")

    def test_recovery_attempt_callback(self):
        """Test recovery attempt callback."""
        callback = Mock()
        self.heartbeat.on_recovery_attempt(callback)

        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_recovery_attempt()

        callback.assert_called_once_with(1)

    def test_recovery_success_callback(self):
        """Test recovery success callback."""
        callback = Mock()
        self.heartbeat.on_recovery_success(callback)

        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_hard_failure()
        self.heartbeat.record_recovery_attempt()
        self.heartbeat.record_recovery_success()

        callback.assert_called_once_with(1)

    def test_get_stats(self):
        """Test statistics snapshot."""
        self.heartbeat.record_soft_failure("Test error")
        stats = self.heartbeat.get_stats()

        self.assertEqual(stats["service"], "TestService")
        self.assertEqual(stats["state"], "HEALTHY")
        self.assertTrue(stats["is_required"])
        self.assertEqual(stats["soft_failures"], 1)
        self.assertEqual(stats["hard_failures"], 0)
        self.assertEqual(stats["last_error"], "Test error")

    def test_reset(self):
        """Test reset clears all state."""
        self.heartbeat.record_soft_failure()
        self.heartbeat.record_soft_failure()
        self.heartbeat.record_hard_failure()

        self.heartbeat.reset()

        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat._soft_failures, 0)
        self.assertEqual(self.heartbeat._hard_failures, 0)
        self.assertEqual(self.heartbeat._recovery_attempts, 0)

    def test_response_time_averaging(self):
        """Test response time averaging."""
        self.heartbeat.record_success(response_time=0.100)
        self.heartbeat.record_success(response_time=0.200)
        self.heartbeat.record_success(response_time=0.300)

        stats = self.heartbeat.get_stats()
        self.assertAlmostEqual(stats["avg_response_time"], 0.2, places=3)

    def test_multiple_callbacks(self):
        """Test multiple callbacks on same event."""
        callback1 = Mock()
        callback2 = Mock()
        self.heartbeat.on_state_change(callback1)
        self.heartbeat.on_state_change(callback2)

        self.heartbeat.record_soft_failure()
        self.heartbeat.record_soft_failure()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_optional_service(self):
        """Test optional service designation."""
        hb = ServiceHeartbeat("Dashboard", is_required=False)
        self.assertFalse(hb.is_required)


class TestServiceQuorumChecker(unittest.TestCase):
    """Tests for ServiceQuorumChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = ServiceQuorumChecker()

    def test_init_default_requirements(self):
        """Test default phase requirements are set."""
        self.assertIn("extraction", self.checker.phase_requirements)
        self.assertIn("measurement", self.checker.phase_requirements)
        self.assertIn("save", self.checker.phase_requirements)

    def test_set_phase_requirements(self):
        """Test setting custom phase requirements."""
        self.checker.set_phase_requirements(
            "custom",
            ["dvc", "database"],
            ServiceQuorumStrategy.ANY_REQUIRED,
        )

        self.assertIn("custom", self.checker.phase_requirements)
        req = self.checker.phase_requirements["custom"]
        self.assertEqual(req["required_services"], ["dvc", "database"])
        self.assertEqual(req["strategy"], ServiceQuorumStrategy.ANY_REQUIRED)

    def test_verify_all_healthy(self):
        """Test verification passes when all required services are healthy."""
        hb1 = ServiceHeartbeat("database")
        hb2 = ServiceHeartbeat("dvc")

        service_map = {"database": hb1, "dvc": hb2}

        passed, msg = self.checker.verify_phase_quorum("extraction", service_map)
        self.assertTrue(passed)

    def test_verify_fails_with_unavailable(self):
        """Test verification fails when required service unavailable."""
        hb1 = ServiceHeartbeat("database")
        hb2 = ServiceHeartbeat("dvc")

        # Make DVC unavailable
        for _ in range(3):
            hb2.record_hard_failure()

        service_map = {"database": hb1, "dvc": hb2}

        # Extraction requires database (ALL_REQUIRED)
        passed, msg = self.checker.verify_phase_quorum("extraction", service_map)
        self.assertTrue(passed)  # Only DB is required for extraction

    def test_verify_all_required_strategy(self):
        """Test ALL_REQUIRED strategy requires all services."""
        hb1 = ServiceHeartbeat("service1")
        hb2 = ServiceHeartbeat("service2")
        hb3 = ServiceHeartbeat("service3")

        # Make one unavailable
        for _ in range(3):
            hb3.record_hard_failure()

        service_map = {"service1": hb1, "service2": hb2, "service3": hb3}

        self.checker.set_phase_requirements(
            "test", ["service1", "service2", "service3"], ServiceQuorumStrategy.ALL_REQUIRED
        )

        passed, msg = self.checker.verify_phase_quorum("test", service_map)
        self.assertFalse(passed)

    def test_verify_any_required_strategy(self):
        """Test ANY_REQUIRED strategy passes if at least one healthy."""
        hb1 = ServiceHeartbeat("service1")
        hb2 = ServiceHeartbeat("service2")

        # Make one unavailable
        for _ in range(3):
            hb2.record_hard_failure()

        service_map = {"service1": hb1, "service2": hb2}

        self.checker.set_phase_requirements(
            "test", ["service1", "service2"], ServiceQuorumStrategy.ANY_REQUIRED
        )

        passed, msg = self.checker.verify_phase_quorum("test", service_map)
        self.assertTrue(passed)

    def test_verify_any_required_all_unavailable(self):
        """Test ANY_REQUIRED fails when all services unavailable."""
        hb1 = ServiceHeartbeat("service1")
        hb2 = ServiceHeartbeat("service2")

        for _ in range(3):
            hb1.record_hard_failure()
            hb2.record_hard_failure()

        service_map = {"service1": hb1, "service2": hb2}

        self.checker.set_phase_requirements(
            "test", ["service1", "service2"], ServiceQuorumStrategy.ANY_REQUIRED
        )

        passed, msg = self.checker.verify_phase_quorum("test", service_map)
        self.assertFalse(passed)

    def test_unknown_phase(self):
        """Test unknown phase returns True (no requirements)."""
        passed, msg = self.checker.verify_phase_quorum("unknown_phase", {})
        self.assertTrue(passed)

    def test_missing_service_in_map(self):
        """Test missing service treated as unhealthy."""
        service_map = {"database": ServiceHeartbeat("database")}

        self.checker.set_phase_requirements(
            "test", ["database", "missing"], ServiceQuorumStrategy.ALL_REQUIRED
        )

        passed, msg = self.checker.verify_phase_quorum("test", service_map)
        self.assertFalse(passed)

    def test_get_phase_status(self):
        """Test getting detailed phase status."""
        hb = ServiceHeartbeat("database")
        service_map = {"database": hb}

        status = self.checker.get_phase_status("extraction", service_map)

        self.assertEqual(status["phase"], "extraction")
        self.assertTrue(status["passed"])
        self.assertIn("status_message", status)
        self.assertEqual(status["required_services"], ["database"])

    def test_status_message_all_healthy(self):
        """Test status message for all healthy services."""
        hb = ServiceHeartbeat("database")
        service_map = {"database": hb}

        passed, msg = self.checker.verify_phase_quorum("extraction", service_map)

        self.assertTrue(passed)
        self.assertIn("OK", msg)
        self.assertIn("healthy", msg)

    def test_status_message_unavailable(self):
        """Test status message for unavailable services."""
        hb = ServiceHeartbeat("database")
        for _ in range(3):
            hb.record_hard_failure()

        service_map = {"database": hb}

        self.checker.set_phase_requirements(
            "test", ["database"], ServiceQuorumStrategy.ALL_REQUIRED
        )

        passed, msg = self.checker.verify_phase_quorum("test", service_map)

        self.assertFalse(passed)
        self.assertIn("FAIL", msg)
        self.assertIn("unavailable", msg)

    def test_log_service_status(self):
        """Test logging service status."""
        hb = ServiceHeartbeat("database")
        service_map = {"database": hb}

        # Should not raise
        self.checker.log_service_status(service_map)

    def test_service_without_heartbeat(self):
        """Test service without heartbeat is treated as healthy."""
        mock_service = Mock()
        service_map = {"custom": mock_service}

        self.checker.set_phase_requirements("test", ["custom"], ServiceQuorumStrategy.ALL_REQUIRED)

        passed, msg = self.checker.verify_phase_quorum("test", service_map)
        self.assertTrue(passed)

    def test_multiple_phases(self):
        """Test verification across multiple phases."""
        db = ServiceHeartbeat("database")
        dvc = ServiceHeartbeat("dvc")
        service_map = {"database": db, "dvc": dvc}

        # Both phases should pass initially
        passed_ext, _ = self.checker.verify_phase_quorum("extraction", service_map)
        self.assertTrue(passed_ext)

        passed_save, _ = self.checker.verify_phase_quorum("save", service_map)
        self.assertTrue(passed_save)

        # Fail DVC, save should still pass (ANY_REQUIRED)
        for _ in range(3):
            dvc.record_hard_failure()

        passed_save, _ = self.checker.verify_phase_quorum("save", service_map)
        self.assertTrue(passed_save)


if __name__ == "__main__":
    unittest.main()
