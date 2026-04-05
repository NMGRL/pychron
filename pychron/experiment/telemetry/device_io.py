"""Device I/O telemetry wrappers for automatic instrumentation.

Provides decorators and context managers for recording telemetry events
when device I/O operations occur (reads, writes, hardware communication).

Usage:
    @telemetry_device_io("extraction_line", "valve_operation")
    def open_valve(self, valve_name):
        # Hardware call here
        pass

    with telemetry_device_io_context("spectrometer", "intensity_read", recorder):
        intensity = spec.get_intensity()
"""

import time
import functools
from typing import Optional, Dict, Any, Callable

from .event import TelemetryEvent, EventType
from .context import TelemetryContext
from .recorder import TelemetryRecorder


def _record_prometheus_device_io_metrics(
    device_name: str,
    operation_type: str,
    duration_seconds: float,
    success: bool,
) -> None:
    """Record Prometheus metrics for device I/O operations.

    Args:
        device_name: Device identifier
        operation_type: Operation identifier
        duration_seconds: Operation duration in seconds
        success: Whether operation succeeded
    """
    try:
        from pychron.observability import (
            inc_counter,
            observe_histogram,
            set_gauge,
        )

        # Normalize label values
        device = str(device_name).lower().replace(" ", "_")[:50]
        operation = str(operation_type).lower().replace(" ", "_")[:50]
        result = "success" if success else "failure"

        # Record counter
        inc_counter(
            "device_io_operations_total",
            "Total device I/O operations",
            labels=["device", "operation", "result"],
            labelvalues={"device": device, "operation": operation, "result": result},
        )

        # Record duration histogram
        observe_histogram(
            "device_io_duration_seconds",
            "Device I/O operation duration",
            duration_seconds,
            labels=["device", "operation"],
            labelvalues={"device": device, "operation": operation},
        )

        # Record last success timestamp (only on success)
        if success:
            set_gauge(
                "device_last_success_timestamp_seconds",
                "Time of last successful device operation",
                time.time(),
                labels=["device"],
                labelvalues={"device": device},
            )
    except Exception as e:
        # Log the exception once per device to avoid spam
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to record Prometheus metrics for {device_name}.{operation_type}: {e}")


def telemetry_device_io(
    device_name: str, operation_type: str, recorder: Optional[TelemetryRecorder] = None
) -> Callable:
    """Decorator for device I/O operations.

    Records device I/O telemetry: operation name, duration, success/failure, and payload.

    Args:
        device_name: Device identifier (e.g., "extraction_line", "spectrometer")
        operation_type: Operation identifier (e.g., "valve_open", "intensity_read")
        recorder: TelemetryRecorder instance (uses global if not provided)

    Returns:
        Decorator function

    Example:
        @telemetry_device_io("extraction_line", "open_valve")
        def open_valve(self, valve_name):
            # Hardware operation
            return True
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not recorder:
                # If no recorder provided, just call the function
                return func(*args, **kwargs)

            # Record device I/O start
            start_time = time.time()
            result = None
            error = None

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                error = str(e)
                success = False
                raise
            finally:
                # Record device I/O end event
                duration_ms = (time.time() - start_time) * 1000
                duration_seconds = duration_ms / 1000.0
                payload = {
                    "device": device_name,
                    "operation": operation_type,
                    "duration_ms": duration_ms,
                    "success": success,
                }

                if error:
                    payload["error"] = error

                # Extract first arg as object context (typically self)
                obj_context = args[0] if args else None
                obj_name = type(obj_context).__name__ if obj_context else "unknown"

                event = TelemetryEvent(
                    event_type=EventType.DEVICE_IO.value,
                    ts=start_time,
                    level="debug" if success else "error",
                    queue_id=TelemetryContext.get_queue_id(),
                    run_id=TelemetryContext.get_run_id(),
                    run_uuid=TelemetryContext.get_run_uuid(),
                    trace_id=TelemetryContext.get_trace_id(),
                    span_id=TelemetryContext.get_current_span_id(),
                    component=f"{device_name}_{obj_name}",
                    action=operation_type,
                    payload=payload,
                )

                recorder.record_event(event)

                # Record Prometheus metrics
                _record_prometheus_device_io_metrics(
                    device_name, operation_type, duration_seconds, success
                )

            return result

        return wrapper

    return decorator


class TelemetryDeviceIOContext:
    """Context manager for device I/O operations.

    Records device I/O telemetry with timing and success/failure tracking.

    Usage:
        with TelemetryDeviceIOContext("spectrometer", "intensity_read", recorder):
            intensity = spec.get_intensity()
    """

    def __init__(
        self,
        device_name: str,
        operation_type: str,
        recorder: Optional[TelemetryRecorder] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Initialize context manager.

        Args:
            device_name: Device identifier
            operation_type: Operation identifier
            recorder: TelemetryRecorder instance
            payload: Additional payload to include in telemetry event
        """
        self.device_name = device_name
        self.operation_type = operation_type
        self.recorder = recorder
        self.payload = payload or {}
        self.start_time = None
        self.success = True
        self.error = None

    def __enter__(self) -> "TelemetryDeviceIOContext":
        """Enter context; record device I/O start."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context; record device I/O end with timing."""
        if not self.recorder:
            return

        if exc_type is not None:
            self.success = False
            self.error = str(exc_val)

        duration_ms = (time.time() - self.start_time) * 1000
        duration_seconds = duration_ms / 1000.0

        payload = self.payload.copy()
        payload.update(
            {
                "device": self.device_name,
                "operation": self.operation_type,
                "duration_ms": duration_ms,
                "success": self.success,
            }
        )

        if self.error:
            payload["error"] = self.error

        event = TelemetryEvent(
            event_type=EventType.DEVICE_IO.value,
            ts=self.start_time,
            level="debug" if self.success else "error",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=TelemetryContext.get_current_span_id(),
            component=self.device_name,
            action=self.operation_type,
            payload=payload,
        )

        self.recorder.record_event(event)

        # Record Prometheus metrics
        _record_prometheus_device_io_metrics(
            self.device_name,
            self.operation_type,
            duration_seconds,
            self.success,
        )

    def set_payload(self, key: str, value: Any) -> None:
        """Update payload during operation (e.g., capture result)."""
        self.payload[key] = value


def telemetry_device_io_context(
    device_name: str,
    operation_type: str,
    recorder: Optional[TelemetryRecorder] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> TelemetryDeviceIOContext:
    """Factory function for device I/O context manager.

    Args:
        device_name: Device identifier
        operation_type: Operation identifier
        recorder: TelemetryRecorder instance
        payload: Optional initial payload

    Returns:
        TelemetryDeviceIOContext instance
    """
    return TelemetryDeviceIOContext(
        device_name=device_name,
        operation_type=operation_type,
        recorder=recorder,
        payload=payload,
    )
