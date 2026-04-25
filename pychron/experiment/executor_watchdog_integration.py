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
- Graceful degradation for degraded health and fail-stop on unavailable devices

Usage:
    executor_watchdog = ExecutorWatchdogIntegration(executor)
    executor_watchdog.initialize_watchdog_system()
    executor_watchdog.check_phase_device_health(phase_name, devices)
    executor_watchdog.check_phase_service_health(phase_name, services)

Design:
    - Non-invasive: All watchdog logic is external to ExperimentExecutor
    - Optional: Only active when PYCHRON_WATCHDOG_ENABLED=true
    - Callback-based: Hooks into executor via public methods
    - Graceful until unavailable: degraded devices warn, unavailable devices halt execution
"""

from typing import Dict, Optional, Any, Tuple
import time
from pychron.globals import globalv
from pychron.core.helpers.logger_setup import new_logger
from pychron.hardware.core.watchdog import HeartbeatState


class ExecutorWatchdogIntegration:
    """Integration point for watchdog/heartbeat monitoring in experiment executor.

    Attributes:
        executor: The ExperimentExecutor instance
        enabled: Whether watchdog system is enabled (from globals)
        logger: Logger instance for debug output
        device_quorum_checker: DeviceQuorumChecker instance (lazy-loaded)
        service_quorum_checker: ServiceQuorumChecker instance (lazy-loaded)
        service_heartbeats: Dict mapping service name to ServiceHeartbeat instance
        recorder: Optional TelemetryRecorder for telemetry emission
    """

    def __init__(self, executor, logger=None, recorder=None):
        """Initialize executor watchdog integration.

        Args:
            executor: ExperimentExecutor instance to monitor
            logger: Optional logger instance (creates new if not provided)
            recorder: Optional TelemetryRecorder instance for telemetry emission
        """
        self.executor = executor
        self.enabled = globalv.watchdog_enabled
        self.logger = logger or new_logger("ExecutorWatchdog")
        self.recorder = recorder

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

            self._device_quorum_checker = DeviceQuorumChecker()
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

        Verifies that required devices for the phase are healthy enough to continue.
        Degraded devices warn. Unavailable devices fail the phase and should stop execution.
        Emits telemetry event for monitoring.

        Args:
            phase_name: Name of experiment phase (e.g., "extraction", "measurement")
            devices: Dict mapping device name to device object (uses executor defaults if None)

        Returns:
            Tuple of (should_continue, status_msg).
        """
        if not self.enabled:
            return True, "Device health check disabled"

        if devices is None:
            devices = self._get_default_devices()

        try:
            phase_status = self.device_quorum_checker.get_phase_status(phase_name, devices)
            device_statuses = phase_status.get("device_statuses", {})
            unavailable = [
                device_name
                for device_name, state in device_statuses.items()
                if state == HeartbeatState.UNAVAILABLE.value
            ]
            degraded = [
                device_name
                for device_name, state in device_statuses.items()
                if state in (HeartbeatState.DEGRADED.value, HeartbeatState.RECOVERING.value)
            ]
            passed = not unavailable
            msg = self._format_device_health_message(
                phase_name,
                unavailable=unavailable,
                degraded=degraded,
                device_statuses=device_statuses,
            )

            # Emit telemetry event for device health check
            if self.recorder:
                self._emit_device_quorum_event(phase_name, passed, msg, devices)

            # Record Prometheus metrics
            self._record_device_health_metrics(phase_name, passed)

            if unavailable:
                self.logger.warning(f"Device health check failed for {phase_name}: {msg}")
                return False, msg

            if degraded:
                self.logger.warning(f"Device health degraded for {phase_name}: {msg}")
            return True, msg
        except Exception as e:
            self.logger.warning(f"Error during device health check for {phase_name}: {e}")

            # Emit telemetry event for device health check error
            if self.recorder:
                self._emit_device_quorum_event(phase_name, False, str(e), devices, error=str(e))

            # Record Prometheus metrics
            self._record_device_health_metrics(phase_name, False)

            # Fail open on instrumentation errors; real device heartbeat failures still surface.
            return True, f"Device health check error: {str(e)}"

    def check_phase_service_health(
        self, phase_name: str, services: Optional[Dict[str, object]] = None
    ) -> Tuple[bool, str]:
        """Check service health before experiment phase.

        Verifies that required services for the phase are available.
        Logs warnings on failure but continues gracefully.
        Emits telemetry event for monitoring.

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

            # Emit telemetry event for service health check
            if self.recorder:
                self._emit_service_quorum_event(phase_name, passed, msg, services)

            # Record Prometheus metrics
            self._record_service_health_metrics(phase_name, passed)

            if not passed:
                self.logger.warning(f"Service health check failed for {phase_name}: {msg}")
                # Graceful degradation: log warning but continue execution
            return True, msg
        except Exception as e:
            self.logger.warning(f"Error during service health check for {phase_name}: {e}")

            # Emit telemetry event for service health check error
            if self.recorder:
                self._emit_service_quorum_event(phase_name, False, str(e), services, error=str(e))

            # Record Prometheus metrics
            self._record_service_health_metrics(phase_name, False)

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

    def _emit_device_quorum_event(
        self,
        phase_name: str,
        passed: bool,
        message: str,
        devices: Dict[str, object],
        error: Optional[str] = None,
    ) -> None:
        """Emit telemetry event for device quorum check."""
        from pychron.experiment.telemetry.event import EventType, TelemetryEvent
        from pychron.experiment.telemetry.context import TelemetryContext

        event = TelemetryEvent(
            event_type=EventType.DEVICE_QUORUM_CHECK.value,
            ts=time.time(),
            level="warning" if not passed else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=TelemetryContext.get_current_span_id(),
            parent_span_id=TelemetryContext.get_parent_span_id(),
            component="watchdog",
            action="device_quorum_check",
            success=passed,
            error=error,
            payload={
                "phase": phase_name,
                "message": message,
                "device_count": len(devices),
                "devices": list(devices.keys()),
            },
        )
        self.recorder.record_event(event)

    def _emit_service_quorum_event(
        self,
        phase_name: str,
        passed: bool,
        message: str,
        services: Dict[str, object],
        error: Optional[str] = None,
    ) -> None:
        """Emit telemetry event for service quorum check."""
        from pychron.experiment.telemetry.event import EventType, TelemetryEvent
        from pychron.experiment.telemetry.context import TelemetryContext

        event = TelemetryEvent(
            event_type=EventType.SERVICE_QUORUM_CHECK.value,
            ts=time.time(),
            level="warning" if not passed else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=TelemetryContext.get_current_span_id(),
            parent_span_id=TelemetryContext.get_parent_span_id(),
            component="watchdog",
            action="service_quorum_check",
            success=passed,
            error=error,
            payload={
                "phase": phase_name,
                "message": message,
                "service_count": len(services),
                "services": list(services.keys()),
            },
        )
        self.recorder.record_event(event)

    def _get_default_devices(self) -> Dict[str, object]:
        """Get default device mapping from executor.

        Returns:
            Dict mapping device name to device manager object
        """
        devices = {}

        spectrometer_device = self._resolve_health_device(self.executor.spectrometer_manager)
        if spectrometer_device:
            devices["spectrometer"] = spectrometer_device
            devices["detector"] = spectrometer_device
            devices["MS"] = spectrometer_device

        extraction_device = self._resolve_health_device(self.executor.extraction_line_manager)
        if extraction_device:
            devices["extraction_line"] = extraction_device
            devices["EL"] = extraction_device

        pump_device = self._resolve_health_device(
            getattr(self.executor.extraction_line_manager, "pump_manager", None)
        )
        if pump_device:
            devices["pump"] = pump_device

        ion_optics_device = self._resolve_health_device(self.executor.ion_optics_manager)
        if ion_optics_device:
            devices["ion_optics"] = ion_optics_device

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

    def _record_device_health_metrics(self, phase_name: str, passed: bool) -> None:
        """Record device health check metrics to Prometheus.

        Args:
            phase_name: Name of the phase
            passed: Whether the health check passed
        """
        try:
            from pychron.observability import inc_counter

            # Normalize phase name
            phase = str(phase_name).lower().replace(" ", "_")[:50]
            kind = "device"

            if not passed:
                inc_counter(
                    "phase_healthcheck_failures_total",
                    "Total phase health check failures",
                    labels=["phase", "kind"],
                    labelvalues={"phase": phase, "kind": kind},
                )
        except Exception:
            pass

    def _record_service_health_metrics(self, phase_name: str, passed: bool) -> None:
        """Record service health check metrics to Prometheus.

        Args:
            phase_name: Name of the phase
            passed: Whether the health check passed
        """
        try:
            from pychron.observability import inc_counter

            # Normalize phase name
            phase = str(phase_name).lower().replace(" ", "_")[:50]
            kind = "service"

            if not passed:
                inc_counter(
                    "phase_healthcheck_failures_total",
                    "Total phase health check failures",
                    labels=["phase", "kind"],
                    labelvalues={"phase": phase, "kind": kind},
                )
        except Exception:
            pass

    def _format_device_health_message(
        self,
        phase_name: str,
        *,
        unavailable: list[str],
        degraded: list[str],
        device_statuses: Dict[str, str],
    ) -> str:
        if unavailable:
            devices = ", ".join(unavailable)
            return f"Communication failure: {devices} unavailable during {phase_name}"
        if degraded:
            devices = ", ".join(degraded)
            return f"Device health degraded during {phase_name}: {devices}"
        if device_statuses:
            return f"Device health healthy for {phase_name}"
        return f"No device health requirements for {phase_name}"

    def _resolve_health_device(
        self,
        obj: Any,
        *,
        _depth: int = 0,
        _visited: Optional[set[int]] = None,
    ) -> Any:
        if obj is None or _depth > 3:
            return None

        if _visited is None:
            _visited = set()

        obj_id = id(obj)
        if obj_id in _visited:
            return None
        _visited.add(obj_id)

        if hasattr(obj, "get_device_health"):
            return obj

        for attr in (
            "microcontroller",
            "controller",
            "spectrometer",
            "laser_controller",
            "temperature_controller",
            "switch_manager",
            "pump_manager",
        ):
            candidate = getattr(obj, attr, None)
            resolved = self._resolve_health_device(candidate, _depth=_depth + 1, _visited=_visited)
            if resolved is not None:
                return resolved

        return None

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
