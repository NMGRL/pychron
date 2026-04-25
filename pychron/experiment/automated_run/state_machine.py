from dataclasses import dataclass, field
from datetime import datetime

from pychron.pychron_constants import (
    CANCELED,
    FAILED,
    TRUNCATED,
    SUCCESS,
    EXTRACTION,
    MEASUREMENT,
    INVALID,
    NOT_RUN,
    ABORTED,
)

STATE_ALIASES = {
    "success": SUCCESS,
    "failed": FAILED,
    "truncated": TRUNCATED,
    "canceled": CANCELED,
    "cancelled": CANCELED,
    "aborted": ABORTED,
    "invalid": INVALID,
    "not run": NOT_RUN,
    "terminated": FAILED,
}

TERMINAL_STATES = {SUCCESS, FAILED, TRUNCATED, CANCELED, ABORTED, INVALID}

EVENT_TARGETS = {
    "reset": NOT_RUN,
    "mark_invalid": INVALID,
    "start_extraction": EXTRACTION,
    "start_measurement": MEASUREMENT,
    "complete": SUCCESS,
    "fail": FAILED,
    "truncate": TRUNCATED,
    "cancel": CANCELED,
    "abort": ABORTED,
}

EVENT_TRANSITIONS = {
    NOT_RUN: {"start_extraction", "start_measurement", "cancel", "fail", "abort", "mark_invalid"},
    EXTRACTION: {"start_measurement", "complete", "fail", "truncate", "cancel", "abort", "mark_invalid"},
    MEASUREMENT: {"complete", "fail", "truncate", "cancel", "abort", "mark_invalid"},
    SUCCESS: set(),
    FAILED: set(),
    TRUNCATED: {"complete"},
    CANCELED: set(),
    INVALID: set(),
    ABORTED: set(),
    "test": set(EVENT_TARGETS),
}


def normalize_state(state):
    if state is None:
        return None
    return STATE_ALIASES.get(state, state)


def normalize_event(event):
    if event is None:
        return None
    return event.lower().strip().replace(" ", "_")


@dataclass
class StateTransition:
    old_state: str
    new_state: str
    event: str
    accepted: bool
    forced: bool = False
    source: str | None = None
    reason: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


class AutomatedRunStateMachine:
    def __init__(self, current_state=NOT_RUN):
        self.current_state = normalize_state(current_state) or NOT_RUN
        self.last_transition = None
        self.history = []

    def is_terminal(self, state=None):
        if state is None:
            state = self.current_state
        return normalize_state(state) in TERMINAL_STATES

    def transition(self, event, force=False, source=None, reason=None):
        event = normalize_event(event)
        current = normalize_state(self.current_state)
        target = EVENT_TARGETS.get(event)
        if event is None or target is None:
            transition = StateTransition(
                old_state=current,
                new_state=current,
                event=event or "",
                accepted=False,
                forced=force,
                source=source,
                reason=reason,
            )
            self.last_transition = transition
            self.history.append(transition)
            return transition

        allowed = EVENT_TRANSITIONS.get(current, set())
        accepted = force or event in allowed or target == current
        new_state = target if accepted else current
        if accepted:
            self.current_state = new_state

        transition = StateTransition(
            old_state=current,
            new_state=new_state,
            event=event,
            accepted=accepted,
            forced=force,
            source=source,
            reason=reason,
        )
        self.last_transition = transition
        self.history.append(transition)
        return transition

    def set_state(self, state, force=False, source=None, reason=None):
        state = normalize_state(state)
        current = normalize_state(self.current_state)
        if state == current:
            return StateTransition(
                old_state=current,
                new_state=current,
                event="noop",
                accepted=True,
                forced=force,
                source=source,
                reason=reason,
            )

        event = next((k for k, v in EVENT_TARGETS.items() if v == state), None)
        if event is None:
            event = normalize_event(state)
        return self.transition(event, force=force, source=source, reason=reason)
