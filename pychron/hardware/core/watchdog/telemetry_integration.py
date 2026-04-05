"""Telemetry integration for device heartbeat monitoring.

This module provides callback-based listeners that integrate device heartbeat
state changes into the existing pychron telemetry system.

Usage:
    from pychron.experiment.telemetry import TelemetryRecorder
    from pychron.hardware.core.watchdog.telemetry_integration import HeartbeatTelemetryListener
    
    recorder = TelemetryRecorder.for_queue("queue_id")
    listener = HeartbeatTelemetryListener(recorder)
    device.heartbeat.on_state_change(listener.on_state_change)
    device.heartbeat.on_failure(listener.on_failure)
    device.heartbeat.on_recovery_attempt(listener.on_recovery_attempt)
    device.heartbeat.on_recovery_success(listener.on_recovery_success)
"""

from typing import Optional
import uuid

from pychron.experiment.telemetry.event import TelemetryEvent, EventType
from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.recorder import TelemetryRecorder


class HeartbeatTelemetryListener:
    """Listens to device heartbeat state changes and emits telemetry events."""

    def __init__(self, recorder: Optional[TelemetryRecorder] = None):
        """Initialize listener.

        Args:
            recorder: Optional TelemetryRecorder instance. If not provided,
                     uses the global recorder (for dependency injection flexibility).
        """
        self.recorder = recorder

    def _get_recorder(self) -> Optional[TelemetryRecorder]:
        """Get the recorder, falling back to global if needed."""
        recorder = self.recorder
        if recorder is None:
            try:
                from pychron.experiment.telemetry.span import _global_recorder

                recorder = _global_recorder
            except (ImportError, AttributeError):
                pass
        return recorder

    def on_state_change(self, device_name: str, old_state: str, new_state: str) -> None:
        """Callback for device health state transitions.

        Args:
            device_name: Name of the device (e.g., "MS", "EL", "pump")
            old_state: Previous health state (e.g., "HEALTHY", "DEGRADED")
            new_state: New health state (e.g., "DEGRADED", "UNAVAILABLE")
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_STATE_CHANGE.value,
            component=f"device_health",
            action="state_transition",
            level="warning" if new_state != "HEALTHY" else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            state_from=old_state,
            state_to=new_state,
            payload={
                "device": device_name,
                "from_state": old_state,
                "to_state": new_state,
            },
        )
        recorder.record_event(event)

    def on_failure(self, device_name: str, failure_count: int, error: Optional[str] = None) -> None:
        """Callback for device failure recording.

        Args:
            device_name: Name of the device
            failure_count: Number of consecutive failures
            error: Error message or exception string
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_FAILURE.value,
            component=f"device_health",
            action="failure",
            level="error",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=False,
            error=error,
            payload={
                "device": device_name,
                "failure_count": failure_count,
                "error": error,
            },
        )
        recorder.record_event(event)

    def on_recovery_attempt(self, device_name: str, attempt_count: int) -> None:
        """Callback for device recovery attempt recording.

        Args:
            device_name: Name of the device
            attempt_count: Number of recovery attempts made
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_RECOVERY_ATTEMPT.value,
            component=f"device_health",
            action="recovery_attempt",
            level="warning",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            payload={
                "device": device_name,
                "attempt_count": attempt_count,
            },
        )
        recorder.record_event(event)

    def on_recovery_success(self, device_name: str, attempt_count: int) -> None:
        """Callback for successful device recovery.

        Args:
            device_name: Name of the device
            attempt_count: Number of recovery attempts it took
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_RECOVERY_SUCCESS.value,
            component=f"device_health",
            action="recovery_success",
            level="info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=True,
            payload={
                "device": device_name,
                "recovery_attempts": attempt_count,
            },
        )
        recorder.record_event(event)

    def on_quorum_check(
        self,
        phase_name: str,
        passed: bool,
        required_devices: list[str],
        healthy_devices: list[str],
        unhealthy_devices: list[str],
    ) -> None:
        """Callback for pre-phase quorum verification.

        Args:
            phase_name: Experiment phase (e.g., "extraction", "measurement")
            passed: Whether quorum check passed
            required_devices: List of required device names
            healthy_devices: List of healthy device names
            unhealthy_devices: List of unhealthy device names
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_QUORUM_CHECK.value,
            component="device_health",
            action="quorum_check",
            level="warning" if not passed else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=passed,
            payload={
                "phase": phase_name,
                "passed": passed,
                "required_devices": required_devices,
                "healthy_devices": healthy_devices,
                "unhealthy_devices": unhealthy_devices,
                "healthy_count": len(healthy_devices),
                "unhealthy_count": len(unhealthy_devices),
            },
        )
        recorder.record_event(event)


class ServiceHealthTelemetryListener:
    """Listens to service heartbeat state changes and emits telemetry events.

    Similar to HeartbeatTelemetryListener but for software services (DVC, DB, etc.)
    """

    def __init__(self, recorder: Optional[TelemetryRecorder] = None):
        """Initialize listener.

        Args:
            recorder: Optional TelemetryRecorder instance. If not provided,
                     uses the global recorder (for dependency injection flexibility).
        """
        self.recorder = recorder

    def _get_recorder(self) -> Optional[TelemetryRecorder]:
        """Get the recorder, falling back to global if needed."""
        recorder = self.recorder
        if recorder is None:
            try:
                from pychron.experiment.telemetry.span import _global_recorder

                recorder = _global_recorder
            except (ImportError, AttributeError):
                pass
        return recorder

    def on_state_change(self, service_name: str, old_state: str, new_state: str) -> None:
        """Callback for service health state transitions.

        Args:
            service_name: Name of the service (e.g., "DVC", "Database")
            old_state: Previous health state (e.g., "HEALTHY", "DEGRADED")
            new_state: New health state (e.g., "DEGRADED", "UNAVAILABLE")
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_STATE_CHANGE.value,
            component="service_health",
            action="state_transition",
            level="warning" if new_state != "HEALTHY" else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            state_from=old_state,
            state_to=new_state,
            payload={
                "service": service_name,
                "from_state": old_state,
                "to_state": new_state,
            },
        )
        recorder.record_event(event)

    def on_failure(
        self, service_name: str, failure_count: int, error: Optional[str] = None
    ) -> None:
        """Callback for service failure recording.

        Args:
            service_name: Name of the service
            failure_count: Number of consecutive failures
            error: Error message or exception string
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_FAILURE.value,
            component="service_health",
            action="failure",
            level="error",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=False,
            error=error,
            payload={
                "service": service_name,
                "failure_count": failure_count,
                "error": error,
            },
        )
        recorder.record_event(event)

    def on_recovery_attempt(self, service_name: str, attempt_count: int) -> None:
        """Callback for service recovery attempt recording.

        Args:
            service_name: Name of the service
            attempt_count: Number of recovery attempts made
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_RECOVERY_ATTEMPT.value,
            component="service_health",
            action="recovery_attempt",
            level="warning",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            payload={
                "service": service_name,
                "attempt_count": attempt_count,
            },
        )
        recorder.record_event(event)

    def on_recovery_success(self, service_name: str, attempt_count: int) -> None:
        """Callback for successful service recovery.

        Args:
            service_name: Name of the service
            attempt_count: Number of recovery attempts it took
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_HEALTH_RECOVERY_SUCCESS.value,
            component="service_health",
            action="recovery_success",
            level="info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=True,
            payload={
                "service": service_name,
                "recovery_attempts": attempt_count,
            },
        )
        recorder.record_event(event)

    def on_service_quorum_check(
        self,
        phase_name: str,
        passed: bool,
        required_services: list[str],
        healthy_services: list[str],
        unhealthy_services: list[str],
    ) -> None:
        """Callback for pre-phase service quorum verification.

        Args:
            phase_name: Experiment phase (e.g., "extraction", "measurement")
            passed: Whether quorum check passed
            required_services: List of required service names
            healthy_services: List of healthy service names
            unhealthy_services: List of unhealthy service names
        """
        recorder = self._get_recorder()
        if recorder is None:
            return

        event = TelemetryEvent.create(
            event_type=EventType.DEVICE_QUORUM_CHECK.value,
            component="service_health",
            action="quorum_check",
            level="warning" if not passed else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_current_span_id(),
            success=passed,
            payload={
                "phase": phase_name,
                "passed": passed,
                "required_services": required_services,
                "healthy_services": healthy_services,
                "unhealthy_services": unhealthy_services,
                "healthy_count": len(healthy_services),
                "unhealthy_count": len(unhealthy_services),
            },
        )
        recorder.record_event(event)
