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

"""Integration of watchdog/heartbeat monitoring into experiment executor.

This module provides executor integration for the watchdog system, enabling:
- Pre-phase device health verification via DeviceQuorumChecker
- Service health monitoring for DVC, database, dashboard via ServiceQuorumChecker
- Automatic initialization of heartbeat instances
- Graceful degradation when health checks fail (logs warnings but continues)

Usage:
    executor_watchdog = ExecutorWatchdogIntegration(executor)
    executor_watchdog.initialize_watchdog_system()
    executor_watchdog.check_phase_device_health(phase_name, devices)
    executor_watchdog.check_phase_service_health(phase_name, services)

Design:
    - Non-invasive: All watchdog logic is external to ExperimentExecutor
    - Optional: Only active when PYCHRON_WATCHDOG_ENABLED=true
    - Callback-based: Hooks into executor via public methods
    - Graceful: Failures log warnings but don't block execution
"""

from typing import Dict, List, Optional, Any, Tuple
from pychron.globals import globalv
from pychron.core.helpers.logger_setup import new_logger


class ExecutorWatchdogIntegration:
    """Integration point for watchdog/heartbeat monitoring in experiment executor.

    Attributes:
        executor: The ExperimentExecutor instance
        enabled: Whether watchdog system is enabled (from globals)
        logger: Logger instance for debug output
        device_quorum_checker: DeviceQuorumChecker instance (lazy-loaded)
        service_quorum_checker: ServiceQuorumChecker instance (lazy-loaded)
        service_heartbeats: Dict mapping service name to ServiceHeartbeat instance
    """

    def __init__(self, executor, logger=None):
        """Initialize executor watchdog integration.

        Args:
            executor: ExperimentExecutor instance to monitor
            logger: Optional logger instance (creates new if not provided)
        """
        self.executor = executor
        self.enabled = globalv.watchdog_enabled
        self.logger = logger or new_logger("ExecutorWatchdog")

        # Lazy-loaded checkers
        self._device_quorum_checker = None
        self._service_quorum_checker = None

        # Service heartbeat instances
        self.service_heartbeats: Dict[str, Any] = {}

    @property
    def device_quorum_checker(self):
        """Lazy-load DeviceQuorumChecker."""
        if self._device_quorum_checker is None:
            from pychron.hardware.core.watchdog import DeviceQuorumChecker

            self._device_quorum_checker = DeviceQuorumChecker(logger=self.logger)
        return self._device_quorum_checker

    @property
    def service_quorum_checker(self):
        """Lazy-load ServiceQuorumChecker."""
        if self._service_quorum_checker is None:
            from pychron.hardware.core.watchdog import ServiceQuorumChecker

            self._service_quorum_checker = ServiceQuorumChecker(logger=self.logger)
        return self._service_quorum_checker

    def initialize_watchdog_system(self) -> bool:
        """Initialize watchdog system and service heartbeat instances.

        This is called once during executor startup to:
        - Create ServiceHeartbeat instances for known services
        - Wire up telemetry listeners
        - Verify services are accessible

        Returns:
            True if successful, False if watchdog is disabled
        """
        if not self.enabled:
            return False

        self.logger.info("Initializing watchdog system")

        # Initialize service heartbeats for known services
        self._initialize_service_heartbeats()

        return True

    def _initialize_service_heartbeats(self) -> None:
        """Create ServiceHeartbeat instances for DVC, database, and dashboard."""
        from pychron.hardware.core.watchdog import ServiceHeartbeat

        # DVC (mainstore)
        if self.executor.datahub and self.executor.datahub.mainstore:
            dvc_hb = ServiceHeartbeat(
                service_name="DVC",
                is_required=bool(self.executor.use_dvc_persistence),
                soft_failure_threshold=3,
                hard_failure_threshold=2,
                logger=self.logger,
            )
            self.service_heartbeats["dvc"] = dvc_hb
            self.logger.debug("Initialized DVC service heartbeat")

        # Dashboard
        if self.executor.dashboard_client:
            dashboard_hb = ServiceHeartbeat(
                service_name="Dashboard",
                is_required=False,  # Dashboard is optional
                soft_failure_threshold=3,
                hard_failure_threshold=2,
                logger=self.logger,
            )
            self.service_heartbeats["dashboard"] = dashboard_hb
            self.logger.debug("Initialized Dashboard service heartbeat")

        # Database (via datahub)
        if self.executor.datahub and self.executor.use_db_persistence:
            db_hb = ServiceHeartbeat(
                service_name="Database",
                is_required=bool(self.executor.use_db_persistence),
                soft_failure_threshold=3,
                hard_failure_threshold=2,
                logger=self.logger,
            )
            self.service_heartbeats["database"] = db_hb
            self.logger.debug("Initialized Database service heartbeat")

    def check_phase_device_health(
        self, phase_name: str, devices: Optional[Dict[str, object]] = None
    ) -> Tuple[bool, str]:
        """Check device health before experiment phase.

        Verifies that required devices for the phase are healthy.
        Logs warnings on failure but continues gracefully.

        Args:
            phase_name: Name of experiment phase (e.g., "extraction", "measurement")
            devices: Dict mapping device name to device object (uses executor defaults if None)

        Returns:
            (passed: bool, status_msg: str) - Always returns (True, msg) for graceful degradation
        """
        if not self.enabled:
            return True, "Device health check disabled"

        if devices is None:
            devices = self._get_default_devices()

        try:
            passed, msg = self.device_quorum_checker.verify_phase_quorum(phase_name, devices)
            if not passed:
                self.logger.warning(f"Device health check failed for {phase_name}: {msg}")
                # Graceful degradation: log warning but continue execution
            return True, msg
        except Exception as e:
            self.logger.warning(f"Error during device health check for {phase_name}: {e}")
            # Graceful degradation: continue on error
            return True, f"Device health check error: {str(e)}"

    def check_phase_service_health(
        self, phase_name: str, services: Optional[Dict[str, object]] = None
    ) -> Tuple[bool, str]:
        """Check service health before experiment phase.

        Verifies that required services for the phase are available.
        Logs warnings on failure but continues gracefully.

        Args:
            phase_name: Name of experiment phase (e.g., "extraction", "measurement", "save")
            services: Dict mapping service name to service object (uses executor defaults if None)

        Returns:
            (passed: bool, status_msg: str) - Always returns (True, msg) for graceful degradation
        """
        if not self.enabled:
            return True, "Service health check disabled"

        if services is None:
            services = self._get_default_services()

        try:
            passed, msg = self.service_quorum_checker.verify_phase_quorum(phase_name, services)
            if not passed:
                self.logger.warning(f"Service health check failed for {phase_name}: {msg}")
                # Graceful degradation: log warning but continue execution
            return True, msg
        except Exception as e:
            self.logger.warning(f"Error during service health check for {phase_name}: {e}")
            # Graceful degradation: continue on error
            return True, f"Service health check error: {str(e)}"

    def record_device_operation(
        self, device_name: str, success: bool, response_time: Optional[float] = None
    ) -> None:
        """Record a device operation for heartbeat tracking.

        Args:
            device_name: Name of device (e.g., "spectrometer", "extraction_line")
            success: Whether operation succeeded
            response_time: Optional response time in seconds
        """
        if not self.enabled:
            return

        # Note: Device heartbeat tracking is handled at the device level
        # This method is a placeholder for future enhancement

    def record_service_operation(
        self,
        service_name: str,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Record a service operation for heartbeat tracking.

        Args:
            service_name: Name of service (e.g., "dvc", "database", "dashboard")
            success: Whether operation succeeded
            response_time: Optional response time in seconds
            error: Optional error message or exception string
        """
        if not self.enabled:
            return

        hb = self.service_heartbeats.get(service_name)
        if hb is None:
            return

        if success:
            hb.record_success(response_time=response_time)
        else:
            # Assume soft failure for unknown errors
            hb.record_soft_failure(error=error)

    def _get_default_devices(self) -> Dict[str, object]:
        """Get default device mapping from executor.

        Returns:
            Dict mapping device name to device manager object
        """
        devices = {}

        if self.executor.spectrometer_manager:
            devices["spectrometer"] = self.executor.spectrometer_manager

        if self.executor.extraction_line_manager:
            devices["extraction_line"] = self.executor.extraction_line_manager

        if self.executor.ion_optics_manager:
            devices["ion_optics"] = self.executor.ion_optics_manager

        return devices

    def _get_default_services(self) -> Dict[str, object]:
        """Get default service mapping from executor.

        Returns:
            Dict mapping service name to service object
        """
        services = {}

        if self.executor.datahub and self.executor.datahub.mainstore:
            services["dvc"] = self.executor.datahub.mainstore

        if self.executor.dashboard_client:
            services["dashboard"] = self.executor.dashboard_client

        if self.executor.datahub and self.executor.use_db_persistence:
            # Database is typically accessed through datahub stores
            for store_name, store in self.executor.datahub.stores.items():
                if store is not None:
                    services[f"database_{store_name}"] = store

        return services

    def log_health_status(self) -> None:
        """Log current device and service health status."""
        if not self.enabled:
            return

        self.logger.info("=== WATCHDOG HEALTH STATUS ===")

        devices = self._get_default_devices()
        if devices:
            self.logger.info("Devices:")
            for device_name, device in devices.items():
                state = self._get_device_state(device)
                self.logger.info(f"  {device_name}: {state}")

        services = self._get_default_services()
        if services:
            self.logger.info("Services:")
            for service_name, service in services.items():
                state = self._get_service_state(service)
                self.logger.info(f"  {service_name}: {state}")

    @staticmethod
    def _get_device_state(device: object) -> str:
        """Get human-readable state of device."""
        try:
            if hasattr(device, "get_state") and callable(getattr(device, "get_state")):
                return str(device.get_state())
            elif hasattr(device, "state"):
                return str(device.state)
            else:
                return "unknown"
        except Exception:
            return "error"

    @staticmethod
    def _get_service_state(service: object) -> str:
        """Get human-readable state of service."""
        try:
            if hasattr(service, "get_state") and callable(getattr(service, "get_state")):
                return str(service.get_state())
            elif hasattr(service, "state"):
                return str(service.state)
            else:
                return "available"
        except Exception:
            return "error"
