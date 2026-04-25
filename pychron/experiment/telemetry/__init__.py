"""Structured telemetry, tracing, and replay for Pychron experiment execution.

This package provides machine-readable observability for experiment execution,
hardware I/O, persistence, and monitor/interlock activity. Telemetry is emitted
as JSON Lines and can be replayed for deterministic incident analysis.

Key exports:
  - TelemetryEvent: Core event schema
  - TelemetryRecorder: JSONL writer with buffering
  - TelemetryContext: Thread-local correlation ID propagation
  - Span: Context manager for timed operations
  - TelemetryLevel: Event severity levels
  - EventType: Enumeration of event types
  - StateMachineListener: Callback for state machine transitions
  - load_telemetry_log: Load events from JSONL file
  - replay_queue_telemetry: Generate incident report from telemetry log
"""

from .event import EventType, TelemetryEvent, TelemetryLevel
from .context import TelemetryContext
from .recorder import TelemetryRecorder
from .span import Span, set_global_recorder
from .state_machine_listener import StateMachineListener
from .replay import load_telemetry_log, replay_queue_telemetry, ReplayReport

__all__ = [
    "EventType",
    "TelemetryEvent",
    "TelemetryLevel",
    "TelemetryContext",
    "TelemetryRecorder",
    "Span",
    "set_global_recorder",
    "StateMachineListener",
    "load_telemetry_log",
    "replay_queue_telemetry",
    "ReplayReport",
]
