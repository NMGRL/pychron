"""Span context manager for timed telemetry operations."""

import time
import uuid
from typing import Optional, Dict, Any

from .event import EventType, TelemetryEvent, TelemetryLevel
from .context import TelemetryContext
from .recorder import TelemetryRecorder


_global_recorder: Optional[TelemetryRecorder] = None


def set_global_recorder(recorder: Optional[TelemetryRecorder]) -> None:
    """Set the global telemetry recorder for spans.

    Call this during executor/queue initialization.
    """
    global _global_recorder
    _global_recorder = recorder


def get_global_recorder() -> Optional[TelemetryRecorder]:
    """Return the current global telemetry recorder."""
    return _global_recorder


class Span:
    """Context manager for timed operations with structured telemetry.

    Automatically records span_start and span_end events with elapsed time,
    success/failure status, and nested parent/child relationships.

    Usage:
        with Span("my_span_id", "component", "action") as span:
            # Do work
            span.record_success(payload={"result": ...})

    Or with automatic timing (no explicit record_success/failure call):
        with Span("my_span_id", "component", "action") as span:
            # Do work; span_end is recorded automatically with success=true
    """

    def __init__(
        self,
        span_id: Optional[str] = None,
        component: str = "unknown",
        action: str = "operation",
        payload: Optional[Dict[str, Any]] = None,
        level: str = "info",
        recorder: Optional[TelemetryRecorder] = None,
    ):
        """Initialize a span.

        Args:
            span_id: Unique span identifier (auto-generated if not provided)
            component: Source component name
            action: Action being performed
            payload: Optional initial payload
            level: Event severity level
            recorder: TelemetryRecorder to use (defaults to global recorder)
        """
        self.span_id = span_id or str(uuid.uuid4())[:8]
        self.component = component
        self.action = action
        self.payload = payload or {}
        self.level = level
        self.recorder = recorder or _global_recorder

        self.start_time = None
        self.end_time = None
        self.duration_ms = None
        self.success = None
        self.error = None
        self._ended = False

    def __enter__(self) -> "Span":
        """Enter context manager; record span_start and push span ID."""
        self.start_time = time.time()

        # Record span_start event
        if self.recorder:
            event = TelemetryEvent(
                event_type=EventType.SPAN_START.value,
                ts=self.start_time,
                level=self.level,
                queue_id=TelemetryContext.get_queue_id(),
                run_id=TelemetryContext.get_run_id(),
                run_uuid=TelemetryContext.get_run_uuid(),
                trace_id=TelemetryContext.get_trace_id(),
                span_id=self.span_id,
                parent_span_id=TelemetryContext.get_current_span_id(),
                component=self.component,
                action=self.action,
                payload=self.payload,
            )
            self.recorder.record_event(event)

        # Push to span stack for nesting
        TelemetryContext.push_span_id(self.span_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager; record span_end with timing."""
        if self._ended:
            return

        # Capture parent span ID BEFORE popping from span stack
        parent_span_id = TelemetryContext.get_parent_span_id()

        # Pop from span stack
        TelemetryContext.pop_span_id()

        assert self.start_time is not None, "Span.__exit__ called without __enter__"
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

        # If no explicit end was recorded, record it now
        if self.success is None:
            if exc_type is not None:
                self.record_failure(
                    reason=exc_type.__name__,
                    error=str(exc_val) if exc_val else None,
                    parent_span_id=parent_span_id,
                )
            else:
                self.record_success(parent_span_id=parent_span_id)

    def record_success(
        self, payload: Optional[Dict[str, Any]] = None, parent_span_id: Optional[str] = None
    ) -> None:
        """Record span_end with success status.

        Args:
            payload: Optional additional payload for the end event
            parent_span_id: Optional parent span ID (from __exit__)
        """
        if self._ended:
            return

        self._ended = True
        self.success = True
        assert self.start_time is not None, "Span.record_success called without __enter__"
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

        if self.recorder:
            end_payload = self.payload.copy()
            if payload:
                end_payload.update(payload)

            event = TelemetryEvent(
                event_type=EventType.SPAN_END.value,
                ts=self.end_time,
                level=self.level,
                queue_id=TelemetryContext.get_queue_id(),
                run_id=TelemetryContext.get_run_id(),
                run_uuid=TelemetryContext.get_run_uuid(),
                trace_id=TelemetryContext.get_trace_id(),
                span_id=self.span_id,
                parent_span_id=parent_span_id or TelemetryContext.get_parent_span_id(),
                component=self.component,
                action=self.action,
                duration_ms=self.duration_ms,
                success=True,
                payload=end_payload,
            )
            self.recorder.record_event(event)

    def record_failure(
        self,
        reason: str,
        error: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> None:
        """Record span_end with failure status.

        Args:
            reason: Failure reason (e.g., "exception", "threshold_exceeded")
            error: Optional error message or exception string
            payload: Optional additional payload
            parent_span_id: Optional parent span ID (from __exit__)
        """
        if self._ended:
            return

        self._ended = True
        self.success = False
        self.error = error
        assert self.start_time is not None, "Span.record_failure called without __enter__"
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

        if self.recorder:
            end_payload = self.payload.copy()
            if payload:
                end_payload.update(payload)

            event = TelemetryEvent(
                event_type=EventType.SPAN_END.value,
                ts=self.end_time,
                level="warning" if reason != "exception" else "error",
                queue_id=TelemetryContext.get_queue_id(),
                run_id=TelemetryContext.get_run_id(),
                run_uuid=TelemetryContext.get_run_uuid(),
                trace_id=TelemetryContext.get_trace_id(),
                span_id=self.span_id,
                parent_span_id=parent_span_id or TelemetryContext.get_parent_span_id(),
                component=self.component,
                action=self.action,
                reason=reason,
                duration_ms=self.duration_ms,
                success=False,
                error=error,
                payload=end_payload,
            )
            self.recorder.record_event(event)
