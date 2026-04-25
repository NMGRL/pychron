"""Telemetry listener for state machine transitions.

This module provides a callback-based listener that can be registered with
ExecutorController to emit structured telemetry for all state transitions.

Usage:
    from pychron.experiment.telemetry import TelemetryRecorder
    from pychron.experiment.telemetry.state_machine_listener import StateMachineListener
    
    recorder = TelemetryRecorder.for_queue("queue_id")
    listener = StateMachineListener(recorder)
    executor_controller.register_on_transition(listener.on_transition)
"""

from typing import Optional
import time
import uuid

from .event import TelemetryEvent, EventType
from .context import TelemetryContext
from .recorder import TelemetryRecorder


class StateMachineListener:
    """Listens to state machine transitions and emits telemetry events."""

    def __init__(self, recorder: Optional[TelemetryRecorder] = None):
        """Initialize listener.

        Args:
            recorder: Optional TelemetryRecorder instance. If not provided,
                     uses the global recorder (for dependency injection flexibility).
        """
        self.recorder = recorder

    def on_transition(self, machine_name: str, record) -> None:
        """Callback for state machine transitions.

        Args:
            machine_name: Name of the machine (e.g., "executor", "queue", "run")
            record: TransitionRecord from the state machine

        Called by ExecutorController._notify() for every transition.
        """
        # Determine recorder to use
        recorder = self.recorder
        if recorder is None:
            from .span import _global_recorder

            recorder = _global_recorder

        if recorder is None:
            return  # No recorder configured

        # Extract relevant data from TransitionRecord
        state_from = getattr(record, "state_from", None)
        state_to = getattr(record, "state_to", None)
        reason = getattr(record, "reason", None)
        accepted = getattr(record, "accepted", True)
        source = getattr(record, "source", None)

        # Get run context if available
        run_id = None
        run_uuid = None
        if machine_name == "run":
            # Try to extract run ID from the transition record
            run_id = getattr(record, "run_id", None)
            run_uuid = getattr(record, "run_uuid", None)

        # Use context if not in record
        if run_id is None:
            run_id = TelemetryContext.get_run_id()
        if run_uuid is None:
            run_uuid = TelemetryContext.get_run_uuid()

        # Get current span for correlation (reuse parent's span_id, not create new)
        current_span_id = TelemetryContext.get_current_span_id()

        # Use record timestamp if available, otherwise use current time
        ts = getattr(record, "ts", None) or time.time()

        # Create telemetry event
        event = TelemetryEvent(
            event_type=EventType.STATE_TRANSITION.value,
            ts=ts,
            level="info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=run_id,
            run_uuid=run_uuid,
            trace_id=TelemetryContext.get_trace_id(),
            span_id=current_span_id or str(uuid.uuid4())[:8],
            parent_span_id=TelemetryContext.get_parent_span_id(),
            component=machine_name,
            action="transition",
            state_from=state_from,
            state_to=state_to,
            reason=reason,
            accepted=accepted,
            payload={
                "machine": machine_name,
                "source": source,
                "record": self._transition_record_to_dict(record),
            },
        )

        recorder.record_event(event)

    @staticmethod
    def _transition_record_to_dict(record) -> dict:
        """Convert TransitionRecord to dictionary for payload."""
        result = {}
        for field in ("state_from", "state_to", "reason", "source", "accepted", "ts"):
            if hasattr(record, field):
                result[field] = getattr(record, field)
        return result
