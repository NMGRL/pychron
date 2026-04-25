"""Structured telemetry event schema and types."""

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional, Dict, Any
import time


class TelemetryLevel(Enum):
    """Event severity levels, matching logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Enumeration of structured event types."""

    # State machine transitions
    STATE_TRANSITION = "state_transition"
    STATE_MACHINE_FINALIZED = "state_machine_finalized"
    STATE_MACHINE_RESET = "state_machine_reset"

    # Span lifecycle
    SPAN_START = "span_start"
    SPAN_END = "span_end"

    # Commands and operations
    COMMAND = "command"
    DEVICE_COMMAND = "device_command"
    DEVICE_IO = "device_io"
    EXECUTION_PROGRESS = "execution_progress"
    STALL_SNAPSHOT = "stall_snapshot"

    # Monitor and interlock
    MONITOR_CHECK = "monitor_check"
    MONITOR_TRIP = "monitor_trip"
    INTERLOCK_CHECK = "interlock_check"
    AUTOMATIC_INTERVENTION = "automatic_intervention"

    # Recovery and failure
    RECOVERY_REQUESTED = "recovery_requested"
    RECOVERY_COMPLETE = "recovery_complete"
    FAILURE_CLASSIFIED = "failure_classified"

    # Device health monitoring
    DEVICE_HEALTH_STATE_CHANGE = "device_health_state_change"
    DEVICE_HEALTH_FAILURE = "device_health_failure"
    DEVICE_HEALTH_RECOVERY_ATTEMPT = "device_health_recovery_attempt"
    DEVICE_HEALTH_RECOVERY_SUCCESS = "device_health_recovery_success"
    DEVICE_QUORUM_CHECK = "device_quorum_check"

    # Service health monitoring
    SERVICE_QUORUM_CHECK = "service_quorum_check"
    SERVICE_HEALTH_STATE_CHANGE = "service_health_state_change"
    SERVICE_HEALTH_FAILURE = "service_health_failure"

    # Session lifecycle
    TELEMETRY_SESSION_START = "telemetry_session_start"
    TELEMETRY_SESSION_END = "telemetry_session_end"


@dataclass
class TelemetryEvent:
    """Core structured telemetry event.

    Attributes:
        event_type: Type of event (see EventType enum)
        ts: Unix timestamp when event occurred
        level: Event severity (see TelemetryLevel)
        queue_id: Experiment/queue name (e.g., "experiment_001")
        run_id: Human-readable run ID (e.g., "sample-001-00-00")
        run_uuid: Machine-readable run UUID (e.g., UUID4 string)
        trace_id: Queue-level correlation ID (same for all runs in queue)
        span_id: Unique identifier for this span/event
        parent_span_id: Span ID of parent span (for nesting)
        component: Source component (e.g., "executor", "queue_machine", "run_machine")
        action: Action performed (e.g., "transition", "start", "save")
        state_from: Previous state (for state_transition events)
        state_to: New state (for state_transition events)
        reason: Reason for event (e.g., "user_cancel", "threshold_exceeded")
        duration_ms: Elapsed time in milliseconds (for span_end events)
        success: Whether operation succeeded (for command/span_end events)
        error: Error message or exception string if failed
        accepted: Whether state transition was accepted (for state_transition)
        payload: Optional structured payload with event-specific data
    """

    event_type: str  # Can be EventType enum value or string
    ts: float
    level: str  # Can be TelemetryLevel enum value or string
    queue_id: Optional[str] = None
    run_id: Optional[str] = None
    run_uuid: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    component: Optional[str] = None
    action: Optional[str] = None
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    reason: Optional[str] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    accepted: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        component: str,
        action: Optional[str] = None,
        level: str = "info",
        **kwargs,
    ) -> "TelemetryEvent":
        """Factory method for creating events with sensible defaults.

        Args:
            event_type: Type of event
            component: Source component
            action: Action performed
            level: Event severity level
            **kwargs: Additional event fields

        Returns:
            TelemetryEvent instance with timestamp set
        """
        return cls(
            event_type=event_type,
            ts=time.time(),
            level=level,
            component=component,
            action=action,
            **kwargs,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert enums to strings
        if isinstance(result["event_type"], EventType):
            result["event_type"] = result["event_type"].value
        if isinstance(result["level"], TelemetryLevel):
            result["level"] = result["level"].value
        return result
