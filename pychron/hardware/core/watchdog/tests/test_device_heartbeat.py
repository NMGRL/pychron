"""Unit tests for DeviceHeartbeat state machine."""

import time
import unittest

from pychron.hardware.core.watchdog.device_heartbeat import (
    DeviceHeartbeat,
    HeartbeatState,
)


class TestDeviceHeartbeat(unittest.TestCase):
    """Test DeviceHeartbeat state machine transitions and behavior."""

    def setUp(self):
        """Create fresh heartbeat for each test."""
        self.heartbeat = DeviceHeartbeat("test_device")

    def test_initial_state_is_healthy(self):
        """Device starts in HEALTHY state."""
        self.assertEqual(self.heartbeat.get_state(), HeartbeatState.HEALTHY)
        self.assertTrue(self.heartbeat.is_healthy())

    def test_success_keeps_healthy(self):
        """Success operation keeps device in HEALTHY state."""
        self.heartbeat.record_success()
        self.assertEqual(self.heartbeat.get_state(), HeartbeatState.HEALTHY)
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 0)

    def test_multiple_successes(self):
        """Multiple successes stay HEALTHY with zero failures."""
        for _ in range(5):
            self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 0)

    def test_one_failure_stays_healthy(self):
        """One failure under threshold stays HEALTHY."""
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 1)

    def test_degraded_threshold_transition(self):
        """Reaching degraded_threshold transitions to DEGRADED."""
        # degraded_threshold defaults to 2
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_healthy())
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_degraded())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 2)

    def test_unavailable_threshold_transition(self):
        """Reaching unavailable_threshold transitions to UNAVAILABLE."""
        # unavailable_threshold defaults to 5
        for _ in range(4):
            self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_degraded())
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_unavailable())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 5)

    def test_success_resets_failures(self):
        """Success resets failure counter and transitions to HEALTHY."""
        self.heartbeat.record_failure()
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_degraded())
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 0)

    def test_recovery_from_degraded(self):
        """Can recover from DEGRADED state via success."""
        self.heartbeat.record_failure()
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_degraded())
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())

    def test_recovery_from_unavailable(self):
        """Can recover from UNAVAILABLE state via success."""
        for _ in range(5):
            self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_unavailable())
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())

    def test_recovery_attempt_enters_recovering(self):
        """record_recovery_attempt transitions to RECOVERING."""
        for _ in range(5):
            self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_unavailable())
        self.heartbeat.record_recovery_attempt()
        self.assertTrue(self.heartbeat.is_recovering())
        self.assertEqual(self.heartbeat.get_recovery_attempts(), 1)

    def test_recovery_success_from_recovering(self):
        """record_recovery_success from RECOVERING goes to HEALTHY."""
        for _ in range(5):
            self.heartbeat.record_failure()
        self.heartbeat.record_recovery_attempt()
        self.assertTrue(self.heartbeat.is_recovering())
        self.heartbeat.record_recovery_success()
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 0)
        self.assertEqual(self.heartbeat.get_recovery_attempts(), 0)

    def test_manual_reset(self):
        """Manual reset transitions to HEALTHY and clears counters."""
        for _ in range(5):
            self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_unavailable())
        self.heartbeat.reset()
        self.assertTrue(self.heartbeat.is_healthy())
        self.assertEqual(self.heartbeat.get_consecutive_failures(), 0)

    def test_time_in_state(self):
        """time_in_state returns reasonable duration."""
        start = time.time()
        time.sleep(0.05)
        duration = self.heartbeat.time_in_state()
        self.assertGreater(duration, 0.04)
        self.assertLess(duration, 0.2)

    def test_time_since_success(self):
        """time_since_success tracks time since last success."""
        self.assertIsNone(self.heartbeat.time_since_success())
        self.heartbeat.record_success()
        time.sleep(0.05)
        duration = self.heartbeat.time_since_success()
        self.assertGreater(duration, 0.04)
        self.assertLess(duration, 0.2)

    def test_custom_thresholds(self):
        """Custom degraded/unavailable thresholds work correctly."""
        hb = DeviceHeartbeat("test", degraded_threshold=1, unavailable_threshold=3)
        hb.record_failure()
        self.assertTrue(hb.is_degraded())
        hb.record_failure()
        self.assertTrue(hb.is_degraded())
        hb.record_failure()
        self.assertTrue(hb.is_unavailable())

    def test_status_summary(self):
        """get_status_summary returns correct dict."""
        self.heartbeat.record_failure()
        self.heartbeat.record_failure()
        summary = self.heartbeat.get_status_summary()
        self.assertEqual(summary["device_id"], "test_device")
        self.assertEqual(summary["state"], "degraded")
        self.assertEqual(summary["consecutive_failures"], 2)
        self.assertEqual(summary["recovery_attempts"], 0)
        self.assertIsNotNone(summary["time_in_state"])
        self.assertIsNone(summary["time_since_success"])

    def test_alternating_success_failure(self):
        """Alternating success/failure properly transitions states."""
        # Success, then failures
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_healthy())
        self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_degraded())
        # Success resets
        self.heartbeat.record_success()
        self.assertTrue(self.heartbeat.is_healthy())
        # More failures
        for _ in range(5):
            self.heartbeat.record_failure()
        self.assertTrue(self.heartbeat.is_unavailable())


if __name__ == "__main__":
    unittest.main()
