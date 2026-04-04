"""Monitor and interlock telemetry wrappers for automated decision tracking.

Provides utilities for recording telemetry events when monitors make decisions
(pausing, skipping, auto-adjusting) or interlocks evaluate conditions.

Usage:
    with telemetry_monitor_decision("pressure", "out_of_range", recorder):
        monitor.pause_run(reason="pressure high")

    with telemetry_interlock_evaluation("sample_weight", result, recorder):
        meets_requirement = check_sample_weight()
"""

import time
from typing import Optional, Dict, Any

from .event import TelemetryEvent, EventType
from .context import TelemetryContext
from .recorder import TelemetryRecorder


class TelemetryMonitorDecision:
    """Context manager for monitor decisions (pause, skip, auto-adjust).

    Records monitor decision telemetry: what check failed, what action taken,
    whether the action succeeded, and relevant context (readings, thresholds).

    Usage:
        with TelemetryMonitorDecision(
            "pressure_monitor",
            "pressure_high",
            {"current_pressure": 50.5, "threshold": 50.0},
            recorder
        ) as monitor_event:
            spec.pause()
            monitor_event.record_action("pause_run", success=True)
    """

    def __init__(
        self,
        monitor_name: str,
        check_type: str,
        context_data: Optional[Dict[str, Any]] = None,
        recorder: Optional[TelemetryRecorder] = None,
    ):
        """Initialize monitor decision context.

        Args:
            monitor_name: Monitor identifier (e.g., "pressure_monitor", "temperature_monitor")
            check_type: Type of check performed (e.g., "pressure_high", "temperature_low")
            context_data: Optional data (readings, thresholds, etc.)
            recorder: TelemetryRecorder instance
        """
        self.monitor_name = monitor_name
        self.check_type = check_type
        self.context_data = context_data or {}
        self.recorder = recorder
        self.start_time = None
        self.action_taken = None
        self.action_success = None

    def __enter__(self) -> "TelemetryMonitorDecision":
        """Enter context; record monitor check start."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context; record monitor decision with action results."""
        if not self.recorder:
            return

        duration_ms = (time.time() - self.start_time) * 1000

        payload = self.context_data.copy()
        payload.update(
            {
                "monitor": self.monitor_name,
                "check_type": self.check_type,
                "duration_ms": duration_ms,
            }
        )

        if self.action_taken:
            payload["action"] = self.action_taken
            if self.action_success is not None:
                payload["action_success"] = self.action_success

        event = TelemetryEvent(
            event_type=EventType.MONITOR_CHECK.value,
            ts=self.start_time,
            level="warning" if exc_type else "info",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=TelemetryContext.get_current_span_id(),
            component=self.monitor_name,
            action=self.check_type,
            payload=payload,
        )

        self.recorder.record_event(event)

    def record_action(self, action: str, success: bool = True) -> None:
        """Record what action was taken by the monitor.

        Args:
            action: Action taken (e.g., "pause_run", "skip_run", "adjust_cryo")
            success: Whether the action succeeded
        """
        self.action_taken = action
        self.action_success = success


class TelemetryInterlockEvaluation:
    """Context manager for interlock condition evaluation.

    Records when interlocks evaluate conditions and whether they pass/fail.

    Usage:
        with TelemetryInterlockEvaluation(
            "sample_weight_check",
            {"sample_weight_min": 5.0, "sample_weight_max": 100.0},
            recorder
        ) as interlock:
            result = check_sample_weight()
            interlock.set_result(result, {"actual_weight": weight})
    """

    def __init__(
        self,
        condition_name: str,
        context_data: Optional[Dict[str, Any]] = None,
        recorder: Optional[TelemetryRecorder] = None,
    ):
        """Initialize interlock evaluation context.

        Args:
            condition_name: Condition identifier (e.g., "sample_weight_check")
            context_data: Optional thresholds/parameters
            recorder: TelemetryRecorder instance
        """
        self.condition_name = condition_name
        self.context_data = context_data or {}
        self.recorder = recorder
        self.start_time = None
        self.result = None
        self.result_data = {}

    def __enter__(self) -> "TelemetryInterlockEvaluation":
        """Enter context; record condition evaluation start."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context; record condition evaluation result."""
        if not self.recorder:
            return

        duration_ms = (time.time() - self.start_time) * 1000

        payload = self.context_data.copy()
        payload.update(
            {
                "condition": self.condition_name,
                "duration_ms": duration_ms,
                "passes": self.result if self.result is not None else (exc_type is None),
            }
        )

        if self.result_data:
            payload.update(self.result_data)

        if exc_type:
            payload["error"] = str(exc_val)

        event = TelemetryEvent(
            event_type=EventType.INTERLOCK_CHECK.value,
            ts=self.start_time,
            level="info" if (self.result is None or self.result) else "warning",
            queue_id=TelemetryContext.get_queue_id(),
            run_id=TelemetryContext.get_run_id(),
            run_uuid=TelemetryContext.get_run_uuid(),
            trace_id=TelemetryContext.get_trace_id(),
            span_id=TelemetryContext.get_current_span_id(),
            component="interlock",
            action=self.condition_name,
            payload=payload,
        )

        self.recorder.record_event(event)

    def set_result(self, passes: bool, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Set the result of the condition evaluation.

        Args:
            passes: Whether the condition passed
            result_data: Optional data (actual values, readings, etc.)
        """
        self.result = passes
        if result_data:
            self.result_data = result_data


def telemetry_monitor_decision(
    monitor_name: str,
    check_type: str,
    context_data: Optional[Dict[str, Any]] = None,
    recorder: Optional[TelemetryRecorder] = None,
) -> TelemetryMonitorDecision:
    """Factory function for monitor decision context manager.

    Args:
        monitor_name: Monitor identifier
        check_type: Type of check
        context_data: Optional context (readings, thresholds)
        recorder: TelemetryRecorder instance

    Returns:
        TelemetryMonitorDecision instance
    """
    return TelemetryMonitorDecision(
        monitor_name=monitor_name,
        check_type=check_type,
        context_data=context_data,
        recorder=recorder,
    )


def telemetry_interlock_evaluation(
    condition_name: str,
    context_data: Optional[Dict[str, Any]] = None,
    recorder: Optional[TelemetryRecorder] = None,
) -> TelemetryInterlockEvaluation:
    """Factory function for interlock evaluation context manager.

    Args:
        condition_name: Condition identifier
        context_data: Optional thresholds/parameters
        recorder: TelemetryRecorder instance

    Returns:
        TelemetryInterlockEvaluation instance
    """
    return TelemetryInterlockEvaluation(
        condition_name=condition_name,
        context_data=context_data,
        recorder=recorder,
    )
