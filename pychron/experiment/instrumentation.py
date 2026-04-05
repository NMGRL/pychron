"""Instrumentation helpers for executor lifecycle metrics.

This module provides functions to record Prometheus metrics for experiment
queue and run lifecycle events.
"""

import time
from typing import Optional


def _record_queue_started(queue_name: Optional[str] = None) -> None:
    """Record that a queue has started.

    Args:
        queue_name: Name of the queue (optional, for debugging).
    """
    try:
        from pychron.observability import inc_counter, set_gauge

        inc_counter(
            "queue_starts_total",
            "Total number of queues started",
        )
        # Increment active queues gauge
        set_gauge(
            "active_queues",
            "Number of active/running queues",
            _get_active_queue_count() + 1,
        )
    except Exception:
        pass


def _record_queue_completed(queue_name: Optional[str] = None) -> None:
    """Record that a queue has completed.

    Args:
        queue_name: Name of the queue (optional, for debugging).
    """
    try:
        from pychron.observability import inc_counter, set_gauge

        inc_counter(
            "queue_completions_total",
            "Total number of queues completed",
        )
        # Decrement active queues gauge
        set_gauge(
            "active_queues",
            "Number of active/running queues",
            max(0, _get_active_queue_count() - 1),
        )
    except Exception:
        pass


def _record_run_started(run_id: Optional[str] = None) -> None:
    """Record that a run has started.

    Args:
        run_id: ID of the run (optional, for debugging).
    """
    try:
        from pychron.observability import inc_counter, set_gauge

        inc_counter(
            "runs_started_total",
            "Total number of runs started",
        )
        # Increment active runs gauge
        set_gauge(
            "active_runs",
            "Number of active/running runs",
            _get_active_run_count() + 1,
        )
    except Exception:
        pass


def _record_run_completed(run_id: Optional[str] = None, duration_seconds: float = 0.0) -> None:
    """Record that a run has completed successfully.

    Args:
        run_id: ID of the run (optional, for debugging).
        duration_seconds: Duration of the run in seconds.
    """
    try:
        from pychron.observability import inc_counter, set_gauge, observe_histogram

        inc_counter(
            "runs_completed_total",
            "Total number of runs completed successfully",
        )
        # Decrement active runs gauge
        set_gauge(
            "active_runs",
            "Number of active/running runs",
            max(0, _get_active_run_count() - 1),
        )
        # Record run duration
        if duration_seconds > 0:
            observe_histogram(
                "run_duration_seconds",
                "Duration of completed runs",
                duration_seconds,
            )
    except Exception:
        pass


def _record_run_failed(run_id: Optional[str] = None, duration_seconds: float = 0.0) -> None:
    """Record that a run has failed.

    Args:
        run_id: ID of the run (optional, for debugging).
        duration_seconds: Duration of the run in seconds before failure.
    """
    try:
        from pychron.observability import inc_counter, set_gauge, observe_histogram

        inc_counter(
            "runs_failed_total",
            "Total number of runs that failed",
        )
        # Decrement active runs gauge
        set_gauge(
            "active_runs",
            "Number of active/running runs",
            max(0, _get_active_run_count() - 1),
        )
        # Record run duration
        if duration_seconds > 0:
            observe_histogram(
                "run_duration_seconds",
                "Duration of completed runs",
                duration_seconds,
            )
    except Exception:
        pass


def _record_run_canceled(run_id: Optional[str] = None, duration_seconds: float = 0.0) -> None:
    """Record that a run has been canceled.

    Args:
        run_id: ID of the run (optional, for debugging).
        duration_seconds: Duration of the run before cancellation.
    """
    try:
        from pychron.observability import inc_counter, set_gauge, observe_histogram

        inc_counter(
            "runs_canceled_total",
            "Total number of runs canceled",
        )
        # Decrement active runs gauge
        set_gauge(
            "active_runs",
            "Number of active/running runs",
            max(0, _get_active_run_count() - 1),
        )
        # Record run duration
        if duration_seconds > 0:
            observe_histogram(
                "run_duration_seconds",
                "Duration of completed runs",
                duration_seconds,
            )
    except Exception:
        pass


def _record_phase_started(phase_name: str) -> None:
    """Record that a phase has started.

    Args:
        phase_name: Name of the phase (e.g., 'extraction', 'measurement').
    """
    # Phase metrics are tracked via context managers by the user
    pass


def _record_phase_duration(phase_name: str, duration_seconds: float) -> None:
    """Record the duration of a completed phase.

    Args:
        phase_name: Name of the phase.
        duration_seconds: Duration in seconds.
    """
    try:
        from pychron.observability import observe_histogram

        # Normalize phase name
        phase = str(phase_name).lower().replace(" ", "_")[:50]

        observe_histogram(
            "phase_duration_seconds",
            "Duration of run phases",
            duration_seconds,
            labels=["phase"],
            labelvalues={"phase": phase},
        )
    except Exception:
        pass


# In-memory tracking for active counts (simplified; in production you'd use Prometheus gauges)
_active_queues = 0
_active_runs = 0


def _get_active_queue_count() -> int:
    """Get current count of active queues.

    Returns:
        Count of active queues.
    """
    global _active_queues
    return max(0, _active_queues)


def _set_active_queue_count(count: int) -> None:
    """Set the count of active queues.

    Args:
        count: New count.
    """
    global _active_queues
    _active_queues = max(0, count)


def _get_active_run_count() -> int:
    """Get current count of active runs.

    Returns:
        Count of active runs.
    """
    global _active_runs
    return max(0, _active_runs)


def _set_active_run_count(count: int) -> None:
    """Set the count of active runs.

    Args:
        count: New count.
    """
    global _active_runs
    _active_runs = max(0, count)
