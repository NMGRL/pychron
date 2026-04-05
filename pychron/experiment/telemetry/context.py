"""Thread-local correlation ID context for telemetry propagation."""

import contextvars
from typing import Optional, List, Union


# Context variables for thread-local storage
_queue_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "telemetry_queue_id", default=None
)
_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "telemetry_trace_id", default=None
)
_run_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "telemetry_run_id", default=None
)
_run_uuid: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "telemetry_run_uuid", default=None
)
_span_stack: contextvars.ContextVar[Optional[List[str]]] = contextvars.ContextVar(
    "telemetry_span_stack", default=None
)


class TelemetryContext:
    """Thread-safe context for correlation IDs and span hierarchy.

    Uses contextvars for thread-local and async-safe storage.
    Provides methods to set/get queue, trace, run IDs and manage span hierarchy.
    """

    @staticmethod
    def set_queue_id(queue_id: Optional[str]) -> None:
        """Set the current queue ID."""
        _queue_id.set(queue_id)

    @staticmethod
    def get_queue_id() -> Optional[str]:
        """Get the current queue ID."""
        return _queue_id.get()

    @staticmethod
    def set_trace_id(trace_id: Optional[str]) -> None:
        """Set the current trace ID (queue-level correlation ID)."""
        _trace_id.set(trace_id)

    @staticmethod
    def get_trace_id() -> Optional[str]:
        """Get the current trace ID."""
        return _trace_id.get()

    @staticmethod
    def set_run_id(run_id: Optional[str]) -> None:
        """Set the current run ID (human-readable)."""
        _run_id.set(run_id)

    @staticmethod
    def get_run_id() -> Optional[str]:
        """Get the current run ID."""
        return _run_id.get()

    @staticmethod
    def set_run_uuid(run_uuid: Optional[str]) -> None:
        """Set the current run UUID (machine-readable)."""
        _run_uuid.set(run_uuid)

    @staticmethod
    def get_run_uuid() -> Optional[str]:
        """Get the current run UUID."""
        return _run_uuid.get()

    @staticmethod
    def push_span_id(span_id: str) -> None:
        """Push a span ID onto the span stack (for nesting)."""
        stack = _span_stack.get()
        if stack is None:
            stack = []
        stack.append(span_id)
        _span_stack.set(stack)

    @staticmethod
    def pop_span_id() -> Optional[str]:
        """Pop the current span ID from the stack."""
        stack = _span_stack.get()
        if stack:
            span_id = stack.pop()
            _span_stack.set(stack)
            return span_id
        return None

    @staticmethod
    def get_current_span_id() -> Optional[str]:
        """Get the current (top of stack) span ID."""
        stack = _span_stack.get()
        if stack:
            return stack[-1]
        return None

    @staticmethod
    def get_parent_span_id() -> Optional[str]:
        """Get the parent span ID (one level below current)."""
        stack = _span_stack.get()
        if stack and len(stack) > 1:
            return stack[-2]
        return None

    @staticmethod
    def clear() -> None:
        """Clear all context (use after queue/experiment completion)."""
        _queue_id.set(None)
        _trace_id.set(None)
        _run_id.set(None)
        _run_uuid.set(None)
        _span_stack.set([])

    @staticmethod
    def clear_all() -> None:
        """Clear all context (alias for clear, use after session completion)."""
        TelemetryContext.clear()
