"""Telemetry log replay and incident report generation."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Dict, List, Any, Optional

from .event import TelemetryEvent, EventType


# Device operation event types (canonical and legacy names)
DEVICE_OPERATION_TYPES = {
    EventType.DEVICE_IO.value,
    EventType.DEVICE_COMMAND.value,  # Backward compat
}

# Watchdog event types
WATCHDOG_EVENT_TYPES = {
    EventType.DEVICE_HEALTH_STATE_CHANGE.value,
    EventType.SERVICE_HEALTH_STATE_CHANGE.value,
    EventType.DEVICE_HEALTH_FAILURE.value,
    EventType.SERVICE_HEALTH_FAILURE.value,
    EventType.DEVICE_QUORUM_CHECK.value,
    EventType.SERVICE_QUORUM_CHECK.value,
}


@dataclass
class StateTransition:
    """Recorded state machine transition."""

    ts: float
    state_from: Optional[str]
    state_to: Optional[str]
    reason: Optional[str]
    accepted: bool


@dataclass
class TimelineEvent:
    """Event in the execution timeline."""

    ts: float
    event_type: str
    component: str
    action: Optional[str]
    span_id: Optional[str]
    duration_ms: Optional[float]
    success: Optional[bool]


@dataclass
class ReplayReport:
    """Deterministic incident report from telemetry log replay.

    Attributes:
        queue_id: Experiment/queue ID
        trace_id: Queue-level trace ID
        timeline: Chronological list of events
        state_machine_history: State transitions per machine
        device_commands: Device command spans
        monitor_history: Monitor check and decision events
        watchdog_events: Device and service health monitoring events
        summary: Human-readable incident summary
    """

    queue_id: str
    trace_id: str
    timeline: List[TimelineEvent] = field(default_factory=list)
    state_machine_history: Dict[str, List[StateTransition]] = field(
        default_factory=lambda: defaultdict(list)
    )
    device_commands: List[Dict[str, Any]] = field(default_factory=list)
    monitor_history: List[Dict[str, Any]] = field(default_factory=list)
    watchdog_events: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


def load_telemetry_log(path: Path) -> Iterable[TelemetryEvent]:
    """Load telemetry events from a JSONL file.

    Args:
        path: Path to JSONL telemetry file

    Yields:
        TelemetryEvent objects parsed from JSON lines

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If a line is not valid JSON
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Telemetry log not found: {path}")

    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                yield TelemetryEvent(**data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num}: {str(e)}", doc=line, pos=e.pos
                )


def replay_queue_telemetry(path: Path) -> ReplayReport:
    """Generate incident report from queue telemetry log.

    Reconstructs the execution timeline, state machine history, device commands,
    and monitor decisions from a telemetry JSONL file.

    Args:
        path: Path to queue-level telemetry JSONL file

    Returns:
        ReplayReport with reconstructed timeline and state history
    """
    events = list(load_telemetry_log(path))

    if not events:
        raise ValueError(f"No events in telemetry log: {path}")

    # Initialize report from first event
    first_event = events[0]
    report = ReplayReport(
        queue_id=first_event.queue_id or "unknown",
        trace_id=first_event.trace_id or "unknown",
    )

    # Process all events
    for event in events:
        # Build timeline
        if event.event_type in ("span_start", "span_end", "state_transition", "command"):
            timeline_event = TimelineEvent(
                ts=event.ts,
                event_type=event.event_type,
                component=event.component or "unknown",
                action=event.action,
                span_id=event.span_id,
                duration_ms=event.duration_ms,
                success=event.success,
            )
            report.timeline.append(timeline_event)

        # Extract state transitions
        if event.event_type == "state_transition":
            machine = event.component or "unknown"
            transition = StateTransition(
                ts=event.ts,
                state_from=event.state_from,
                state_to=event.state_to or "unknown",
                reason=event.reason,
                accepted=event.accepted or True,
            )
            report.state_machine_history[machine].append(transition)

        # Extract device commands (both canonical and legacy names)
        if event.event_type in DEVICE_OPERATION_TYPES:
            report.device_commands.append(
                {
                    "ts": event.ts,
                    "component": event.component,
                    "action": event.action,
                    "success": event.success,
                    "duration_ms": event.duration_ms,
                    "payload": event.payload,
                }
            )

        # Extract monitor/interlock decisions
        if event.event_type in (
            "monitor_check",
            "monitor_trip",
            "interlock_check",
            "automatic_intervention",
        ):
            report.monitor_history.append(
                {
                    "ts": event.ts,
                    "event_type": event.event_type,
                    "reason": event.reason,
                    "payload": event.payload,
                }
            )

        # Extract watchdog events (device and service health)
        if event.event_type in WATCHDOG_EVENT_TYPES:
            report.watchdog_events.append(
                {
                    "ts": event.ts,
                    "event_type": event.event_type,
                    "component": event.component,
                    "action": event.action,
                    "success": event.success,
                    "phase": event.payload.get("phase") if event.payload else None,
                    "message": event.payload.get("message") if event.payload else None,
                    "payload": event.payload,
                }
            )

    # Generate summary
    report.summary = _generate_incident_summary(report)

    return report


def _generate_incident_summary(report: ReplayReport) -> str:
    """Generate human-readable incident summary from replay report."""
    lines = [
        f"Queue: {report.queue_id}",
        f"Trace ID: {report.trace_id}",
        f"Timeline events: {len(report.timeline)}",
        f"State machines: {len(report.state_machine_history)}",
    ]

    # Add state machine summary
    for machine, transitions in report.state_machine_history.items():
        if transitions:
            final_state = transitions[-1].state_to
            lines.append(f"  {machine}: {final_state}")

    # Add device command summary
    if report.device_commands:
        failed = sum(1 for cmd in report.device_commands if not cmd.get("success", True))
        lines.append(f"Device commands: {len(report.device_commands)} ({failed} failed)")

    # Add monitor summary
    if report.monitor_history:
        lines.append(f"Monitor/Interlock events: {len(report.monitor_history)}")

    # Add watchdog summary
    if report.watchdog_events:
        lines.append(f"Watchdog/Health events: {len(report.watchdog_events)}")

    return "\n".join(lines)


def replay_run_telemetry(path: Path) -> ReplayReport:
    """Generate incident report from run-level telemetry log.

    Similar to replay_queue_telemetry but for a single run.

    Args:
        path: Path to run-level telemetry JSONL file

    Returns:
        ReplayReport with reconstructed run timeline
    """
    # For now, same as queue replay
    return replay_queue_telemetry(path)
