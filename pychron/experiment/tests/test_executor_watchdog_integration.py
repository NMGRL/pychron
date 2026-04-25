# ===============================================================================
# Copyright 2024 Pychron Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

"""Integration tests for executor watchdog integration.

Tests verify:
- Watchdog initialization and lifecycle
- Phase health check integration (extraction, measurement, save)
- Graceful degradation on health check failures
- Service heartbeat tracking
- Device health verification
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pychron.experiment.executor_watchdog_integration import ExecutorWatchdogIntegration


class TestExecutorWatchdogIntegration(unittest.TestCase):
    """Tests for ExecutorWatchdogIntegration."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = Mock()
        self.executor.datahub = Mock()
        self.executor.datahub.mainstore = Mock()
        self.executor.datahub.stores = {}
        self.executor.use_dvc_persistence = True
        self.executor.use_db_persistence = True
        self.executor.dashboard_client = Mock()
        self.executor.spectrometer_manager = Mock()
        self.executor.extraction_line_manager = Mock()
        self.executor.ion_optics_manager = Mock()

    def test_init(self):
        """Test watchdog initialization."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            self.assertEqual(watchdog.executor, self.executor)
            self.assertFalse(watchdog.enabled)

    def test_init_enabled(self):
        """Test watchdog initialization when enabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            self.assertTrue(watchdog.enabled)

    def test_initialize_watchdog_disabled(self):
        """Test watchdog initialization when disabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            result = watchdog.initialize_watchdog_system()
            self.assertFalse(result)

    def test_initialize_watchdog_enabled(self):
        """Test watchdog initialization when enabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            result = watchdog.initialize_watchdog_system()
            self.assertTrue(result)

    def test_initialize_service_heartbeats(self):
        """Test service heartbeat initialization."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            watchdog._initialize_service_heartbeats()

            # Should have DVC, Dashboard, and Database heartbeats
            self.assertIn("dvc", watchdog.service_heartbeats)
            self.assertIn("dashboard", watchdog.service_heartbeats)
            self.assertIn("database", watchdog.service_heartbeats)

    def test_lazy_load_device_quorum_checker(self):
        """Test lazy-loading of device quorum checker."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # First access should create the checker
            checker1 = watchdog.device_quorum_checker
            checker2 = watchdog.device_quorum_checker

            # Should return the same instance
            self.assertIs(checker1, checker2)

    def test_lazy_load_service_quorum_checker(self):
        """Test lazy-loading of service quorum checker."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # First access should create the checker
            checker1 = watchdog.service_quorum_checker
            checker2 = watchdog.service_quorum_checker

            # Should return the same instance
            self.assertIs(checker1, checker2)

    def test_check_phase_device_health_disabled(self):
        """Test device health check when watchdog disabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            passed, msg = watchdog.check_phase_device_health("extraction")
            self.assertTrue(passed)
            self.assertIn("disabled", msg.lower())

    def test_check_phase_device_health_enabled(self):
        """Test device health check when watchdog enabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # Mock the quorum checker
            watchdog._device_quorum_checker = Mock()
            watchdog._device_quorum_checker.get_phase_status.return_value = {
                "device_statuses": {"spectrometer": "healthy"},
            }

            passed, msg = watchdog.check_phase_device_health("extraction")
            self.assertTrue(passed)

    def test_check_phase_device_health_failure_when_unavailable(self):
        """Unavailable device should fail the health check."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # Mock the quorum checker to return unavailable device
            watchdog._device_quorum_checker = Mock()
            watchdog._device_quorum_checker.get_phase_status.return_value = {
                "device_statuses": {"spectrometer": "unavailable"},
            }

            passed, msg = watchdog.check_phase_device_health("extraction")
            self.assertFalse(passed)
            self.assertIn("unavailable", msg.lower())

    def test_check_phase_service_health_disabled(self):
        """Test service health check when watchdog disabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            passed, msg = watchdog.check_phase_service_health("save")
            self.assertTrue(passed)
            self.assertIn("disabled", msg.lower())

    def test_check_phase_service_health_enabled(self):
        """Test service health check when watchdog enabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # Mock the quorum checker
            watchdog._service_quorum_checker = Mock()
            watchdog._service_quorum_checker.verify_phase_quorum.return_value = (
                True,
                "Services healthy",
            )

            passed, msg = watchdog.check_phase_service_health("save")
            self.assertTrue(passed)

    def test_check_phase_service_health_failure_graceful(self):
        """Test service health check failure is graceful."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)

            # Mock the quorum checker to return failure
            watchdog._service_quorum_checker = Mock()
            watchdog._service_quorum_checker.verify_phase_quorum.return_value = (
                False,
                "Service health check failed",
            )

            # Should still return True (graceful degradation)
            passed, msg = watchdog.check_phase_service_health("save")
            self.assertTrue(passed)
            self.assertIn("failed", msg.lower())

    def test_record_service_operation_disabled(self):
        """Test service operation recording when watchdog disabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            # Should not raise exception
            watchdog.record_service_operation("dvc", True, response_time=0.5)

    def test_record_service_operation_success(self):
        """Test recording successful service operation."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            watchdog._initialize_service_heartbeats()

            # Record success
            watchdog.record_service_operation("dvc", True, response_time=0.5)

            # Heartbeat should record success
            hb = watchdog.service_heartbeats["dvc"]
            stats = hb.get_stats()
            self.assertEqual(stats["soft_failures"], 0)
            self.assertEqual(stats["hard_failures"], 0)
            self.assertIsNone(stats["last_error"])

    def test_record_service_operation_failure(self):
        """Test recording failed service operation."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            watchdog._initialize_service_heartbeats()

            # Record failure
            watchdog.record_service_operation("dvc", False, error="Connection timeout")

            # Heartbeat should record failure
            hb = watchdog.service_heartbeats["dvc"]
            self.assertGreater(hb._soft_failures, 0)

    def test_get_default_devices(self):
        """Test getting default device mapping."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            devices = watchdog._get_default_devices()

            self.assertIn("spectrometer", devices)
            self.assertIn("extraction_line", devices)
            self.assertIn("ion_optics", devices)

    def test_get_default_services(self):
        """Test getting default service mapping."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            services = watchdog._get_default_services()

            self.assertIn("dvc", services)
            self.assertIn("dashboard", services)

    def test_get_device_state_with_get_state_method(self):
        """Test getting device state via get_state method."""
        device = Mock()
        device.get_state.return_value = "HEALTHY"

        state = ExecutorWatchdogIntegration._get_device_state(device)
        self.assertEqual(state, "HEALTHY")

    def test_get_device_state_with_state_attribute(self):
        """Test getting device state via state attribute."""
        device = Mock()
        device.get_state = None
        device.state = "RUNNING"

        state = ExecutorWatchdogIntegration._get_device_state(device)
        self.assertEqual(state, "RUNNING")

    def test_get_device_state_unknown(self):
        """Test getting device state when unknown."""
        device = Mock(spec=[])  # No get_state or state

        state = ExecutorWatchdogIntegration._get_device_state(device)
        self.assertEqual(state, "unknown")

    def test_get_device_state_error(self):
        """Test getting device state when error occurs."""
        device = Mock()
        device.get_state.side_effect = RuntimeError("Connection error")

        state = ExecutorWatchdogIntegration._get_device_state(device)
        self.assertEqual(state, "error")

    def test_get_service_state_with_get_state_method(self):
        """Test getting service state via get_state method."""
        service = Mock()
        service.get_state.return_value = "AVAILABLE"

        state = ExecutorWatchdogIntegration._get_service_state(service)
        self.assertEqual(state, "AVAILABLE")

    def test_get_service_state_available(self):
        """Test getting service state when available."""
        service = Mock(spec=[])  # No get_state or state

        state = ExecutorWatchdogIntegration._get_service_state(service)
        self.assertEqual(state, "available")

    def test_get_service_state_error(self):
        """Test getting service state when error occurs."""
        service = Mock()
        service.get_state.side_effect = RuntimeError("Connection error")

        state = ExecutorWatchdogIntegration._get_service_state(service)
        self.assertEqual(state, "error")

    def test_log_health_status_disabled(self):
        """Test logging health status when watchdog disabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = False
            watchdog = ExecutorWatchdogIntegration(self.executor)
            # Should not raise exception
            watchdog.log_health_status()

    def test_log_health_status_enabled(self):
        """Test logging health status when watchdog enabled."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            # Should not raise exception
            watchdog.log_health_status()


class TestExecutorWatchdogPropertyAccess(unittest.TestCase):
    """Tests for watchdog property access patterns."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = Mock()
        self.executor.datahub = Mock()
        self.executor.datahub.mainstore = Mock()
        self.executor.datahub.stores = {}

    def test_resolve_health_device_returns_none_for_unknown(self):
        """Unknown objects should not resolve to heartbeat-capable devices."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            device = object()

            self.assertIsNone(watchdog._resolve_health_device(device))

    def test_check_with_custom_devices(self):
        """Test health check with custom device mapping."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            watchdog._device_quorum_checker = Mock()
            watchdog._device_quorum_checker.get_phase_status.return_value = {
                "device_statuses": {"custom_device": "healthy"},
            }

            custom_devices = {"custom_device": Mock()}
            passed, msg = watchdog.check_phase_device_health("extraction", devices=custom_devices)

            watchdog._device_quorum_checker.get_phase_status.assert_called_once_with(
                "extraction", custom_devices
            )

    def test_check_with_custom_services(self):
        """Test health check with custom service mapping."""
        with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
            mock_globalv.watchdog_enabled = True
            watchdog = ExecutorWatchdogIntegration(self.executor)
            watchdog._service_quorum_checker = Mock()
            watchdog._service_quorum_checker.verify_phase_quorum.return_value = (
                True,
                "All good",
            )

            custom_services = {"custom_service": Mock()}
            passed, msg = watchdog.check_phase_service_health("save", services=custom_services)

            # Verify custom services were used
            watchdog._service_quorum_checker.verify_phase_quorum.assert_called_once_with(
                "save", custom_services
            )


if __name__ == "__main__":
    unittest.main()
