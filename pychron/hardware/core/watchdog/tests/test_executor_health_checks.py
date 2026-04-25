"""Unit tests for executor health checks and device quorum verification."""

import unittest

from pychron.hardware.core.watchdog import DeviceHeartbeat, HeartbeatState
from pychron.hardware.core.watchdog.executor_health_checks import (
    DeviceQuorumChecker,
    log_device_status,
)


class MockDevice:
    """Mock device with optional heartbeat."""

    def __init__(self, name: str, health_state: HeartbeatState | None = None):
        self.name = name
        self._heartbeat = None
        if health_state is not None:
            self._heartbeat = DeviceHeartbeat(name)
            if health_state == HeartbeatState.HEALTHY:
                self._heartbeat.record_success()
            elif health_state == HeartbeatState.DEGRADED:
                self._heartbeat.record_failure()
                self._heartbeat.record_failure()
            elif health_state == HeartbeatState.UNAVAILABLE:
                for _ in range(5):
                    self._heartbeat.record_failure()
            elif health_state == HeartbeatState.RECOVERING:
                for _ in range(5):
                    self._heartbeat.record_failure()
                self._heartbeat.record_recovery_attempt()

    def get_device_health(self):
        if self._heartbeat:
            return self._heartbeat.get_state()
        return None


class TestDeviceQuorumChecker(unittest.TestCase):
    """Test quorum verification logic."""

    def setUp(self):
        """Create checker with default requirements."""
        self.checker = DeviceQuorumChecker()

    def test_all_healthy_passes(self):
        """All required devices HEALTHY passes all_healthy strategy."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.HEALTHY),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertTrue(passed)
        self.assertIn("extraction", msg)

    def test_one_degraded_all_healthy_fails(self):
        """One degraded device fails all_healthy strategy."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.DEGRADED),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertFalse(passed)
        self.assertIn("EL", msg)
        self.assertIn("DEGRADED", msg)

    def test_one_unavailable_all_healthy_fails(self):
        """One unavailable device fails all_healthy strategy."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.UNAVAILABLE),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertFalse(passed)
        self.assertIn("UNAVAILABLE", msg)

    def test_any_healthy_passes_with_one(self):
        """One healthy device passes any_healthy strategy."""
        devices = {
            "database": MockDevice("database", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("save", devices)
        self.assertTrue(passed)

    def test_any_healthy_fails_none(self):
        """No healthy devices fails any_healthy strategy."""
        devices = {
            "database": MockDevice("database", HeartbeatState.UNAVAILABLE),
        }
        passed, msg = self.checker.verify_phase_quorum("save", devices)
        self.assertFalse(passed)

    def test_any_healthy_passes_with_degraded(self):
        """any_healthy passes if at least one healthy (ignores degraded)."""
        devices = {
            "database": MockDevice("database", HeartbeatState.HEALTHY),
            "dvc": MockDevice("dvc", HeartbeatState.DEGRADED),
        }
        passed, msg = self.checker.verify_phase_quorum("save", devices)
        self.assertTrue(passed)

    def test_missing_required_device(self):
        """Missing required device fails verification."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
            # "EL" is missing
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertFalse(passed)
        self.assertIn("NOT_FOUND", msg)

    def test_unknown_phase(self):
        """Unknown phase is allowed (no requirements)."""
        devices = {}
        passed, msg = self.checker.verify_phase_quorum("unknown_phase", devices)
        self.assertTrue(passed)

    def test_device_without_heartbeat(self):
        """Device without heartbeat support is treated as healthy."""
        devices = {
            "MS": MockDevice("MS", None),  # No heartbeat - treat as healthy
            "EL": MockDevice("EL", HeartbeatState.HEALTHY),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        # Device without heartbeat (MS) returns None, should count as healthy
        self.assertTrue(passed)

    def test_recovering_device(self):
        """RECOVERING device counts as unhealthy for all_healthy."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.RECOVERING),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertFalse(passed)

    def test_get_phase_status(self):
        """get_phase_status returns detailed status dict."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.DEGRADED),
            "pump": MockDevice("pump", HeartbeatState.HEALTHY),
        }
        status = self.checker.get_phase_status("extraction", devices)
        self.assertEqual(status["phase_name"], "extraction")
        self.assertEqual(status["strategy"], "all_healthy")
        self.assertEqual(status["healthy_count"], 2)
        self.assertEqual(status["total_count"], 3)
        self.assertFalse(status["passed"])
        self.assertEqual(status["device_statuses"]["MS"], "healthy")
        self.assertEqual(status["device_statuses"]["EL"], "degraded")

    def test_custom_phase_requirements(self):
        """Custom phase requirements override defaults."""
        custom_reqs = {
            "custom_phase": {
                "required_devices": ["device_a", "device_b"],
                "strategy": "all_healthy",
            }
        }
        checker = DeviceQuorumChecker(custom_reqs)
        devices = {
            "device_a": MockDevice("device_a", HeartbeatState.HEALTHY),
            "device_b": MockDevice("device_b", HeartbeatState.HEALTHY),
        }
        # Test custom phase requirements work
        passed, msg = checker.verify_phase_quorum("custom_phase", devices)
        self.assertTrue(passed)
        # extraction not in custom reqs, so should pass (no requirements)
        passed2, msg2 = checker.verify_phase_quorum("extraction", devices)
        self.assertTrue(passed2)

    def test_status_message_format(self):
        """Status message includes all device states."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.UNAVAILABLE),
        }
        passed, msg = self.checker.verify_phase_quorum("extraction", devices)
        self.assertIn("extraction", msg)
        self.assertIn("all_healthy", msg)
        self.assertIn("MS:", msg)
        self.assertIn("HEALTHY", msg)
        self.assertIn("EL:", msg)
        self.assertIn("UNAVAILABLE", msg)


class TestLogDeviceStatus(unittest.TestCase):
    """Test device status logging."""

    def test_log_device_status_with_heartbeat(self):
        """log_device_status reports devices with heartbeat."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "EL": MockDevice("EL", HeartbeatState.DEGRADED),
        }
        status = log_device_status(devices)
        self.assertIn("Device Health Status:", status)
        self.assertIn("MS:", status)
        self.assertIn("HEALTHY", status)
        self.assertIn("EL:", status)
        self.assertIn("DEGRADED", status)

    def test_log_device_status_without_heartbeat(self):
        """log_device_status notes devices without heartbeat."""
        devices = {
            "olddevice": MockDevice("olddevice", None),
        }
        status = log_device_status(devices)
        self.assertIn("olddevice:", status)
        self.assertIn("NO_HEARTBEAT", status)

    def test_log_device_status_mixed(self):
        """log_device_status handles mixed heartbeat support."""
        devices = {
            "MS": MockDevice("MS", HeartbeatState.HEALTHY),
            "legacy": MockDevice("legacy", None),
            "pump": MockDevice("pump", HeartbeatState.UNAVAILABLE),
        }
        status = log_device_status(devices)
        self.assertIn("MS:", status)
        self.assertIn("legacy:", status)
        self.assertIn("pump:", status)
        self.assertIn("NO_HEARTBEAT", status)
        self.assertIn("UNAVAILABLE", status)


if __name__ == "__main__":
    unittest.main()
