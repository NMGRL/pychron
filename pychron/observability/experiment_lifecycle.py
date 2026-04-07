"""Experiment lifecycle metrics recording.

This module provides functions to record key experiment lifecycle events
(queue start/completion, run start/completion, extraction/measurement phases)
as Prometheus metrics and observable events.

Events are recorded with appropriate labels (queue_name, run_id, status, etc.)
and displayed in the Prometheus Observability UI.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict

from pychron.observability import event_capture

logger = logging.getLogger(__name__)


def record_queue_started(queue_name: str, num_runs: int = 1) -> None:
    """Record that a queue execution has started.

    Args:
        queue_name: Name of the queue
        num_runs: Number of runs in the queue
    """
    logger.debug(f"Recording queue started: {queue_name} ({num_runs} runs)")
    event_capture.add_event(
        event_type="counter",
        metric_name="queue_started",
        value=1.0,
        labels={"queue": queue_name, "runs": str(num_runs)},
        status="success",
    )


def record_queue_completed(queue_name: str, status: str = "success") -> None:
    """Record that a queue execution has completed.

    Args:
        queue_name: Name of the queue
        status: Completion status (success, failed, canceled, aborted)
    """
    logger.debug(f"Recording queue completed: {queue_name} - {status}")
    event_capture.add_event(
        event_type="counter",
        metric_name="queue_completed",
        value=1.0,
        labels={"queue": queue_name, "status": status},
        status="success",
    )


def record_run_started(
    queue_name: str,
    run_id: str,
    sample: Optional[str] = None,
    material: Optional[str] = None,
) -> None:
    """Record that a run has started.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        sample: Sample identifier (optional)
        material: Material type (optional)
    """
    labels = {"queue": queue_name, "run_id": run_id}
    if sample:
        labels["sample"] = sample
    if material:
        labels["material"] = material

    logger.debug(f"Recording run started: {queue_name}/{run_id}")
    event_capture.add_event(
        event_type="counter",
        metric_name="run_started",
        value=1.0,
        labels=labels,
        status="success",
    )


def record_run_completed(queue_name: str, run_id: str, status: str = "success") -> None:
    """Record that a run has completed.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        status: Completion status (success, failed, invalid, canceled)
    """
    logger.debug(f"Recording run completed: {queue_name}/{run_id} - {status}")
    event_capture.add_event(
        event_type="counter",
        metric_name="run_completed",
        value=1.0,
        labels={"queue": queue_name, "run_id": run_id, "status": status},
        status="success",
    )


def record_extraction_started(
    queue_name: str, run_id: str, extraction_type: Optional[str] = None
) -> None:
    """Record that extraction phase has started.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        extraction_type: Type of extraction (laser, furnace, etc.)
    """
    labels = {"queue": queue_name, "run_id": run_id}
    if extraction_type:
        labels["type"] = extraction_type

    logger.debug(f"Recording extraction started: {queue_name}/{run_id}")
    event_capture.add_event(
        event_type="counter",
        metric_name="extraction_started",
        value=1.0,
        labels=labels,
        status="success",
    )


def record_extraction_completed(queue_name: str, run_id: str, status: str = "success") -> None:
    """Record that extraction phase has completed.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        status: Completion status (success, failed)
    """
    logger.debug(f"Recording extraction completed: {queue_name}/{run_id} - {status}")
    event_capture.add_event(
        event_type="counter",
        metric_name="extraction_completed",
        value=1.0,
        labels={"queue": queue_name, "run_id": run_id, "status": status},
        status="success",
    )


def record_measurement_started(queue_name: str, run_id: str) -> None:
    """Record that measurement phase has started.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
    """
    logger.debug(f"Recording measurement started: {queue_name}/{run_id}")
    event_capture.add_event(
        event_type="counter",
        metric_name="measurement_started",
        value=1.0,
        labels={"queue": queue_name, "run_id": run_id},
        status="success",
    )


def record_measurement_completed(queue_name: str, run_id: str, status: str = "success") -> None:
    """Record that measurement phase has completed.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        status: Completion status (success, failed)
    """
    logger.debug(f"Recording measurement completed: {queue_name}/{run_id} - {status}")
    event_capture.add_event(
        event_type="counter",
        metric_name="measurement_completed",
        value=1.0,
        labels={"queue": queue_name, "run_id": run_id, "status": status},
        status="success",
    )


def record_analysis_complete(queue_name: str, run_id: str, n_peaks: int = 0) -> None:
    """Record that data analysis has completed.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        n_peaks: Number of peaks detected
    """
    logger.debug(f"Recording analysis complete: {queue_name}/{run_id} ({n_peaks} peaks)")
    event_capture.add_event(
        event_type="counter",
        metric_name="analysis_complete",
        value=1.0,
        labels={"queue": queue_name, "run_id": run_id, "n_peaks": str(n_peaks)},
        status="success",
    )


def record_age_calculated(
    queue_name: str, run_id: str, age: float, material: Optional[str] = None
) -> None:
    """Record that age has been calculated.

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
        age: Calculated age value
        material: Material type (optional)
    """
    labels = {"queue": queue_name, "run_id": run_id}
    if material:
        labels["material"] = material

    logger.debug(f"Recording age calculated: {queue_name}/{run_id} = {age}")
    event_capture.add_event(
        event_type="gauge",
        metric_name="age_calculated",
        value=age,
        labels=labels,
        status="success",
    )


@contextmanager
def record_phase_duration(
    phase_name: str, queue_name: str, run_id: str, labels: Optional[Dict[str, str]] = None
):
    """Context manager to record duration of a phase.

    Usage:
        with record_phase_duration("extraction", queue, run):
            # do extraction work
            pass

    Args:
        phase_name: Name of the phase (extraction, measurement, etc.)
        queue_name: Name of the queue
        run_id: Unique run identifier
        labels: Additional labels to include
    """
    start = time.monotonic()
    phase_labels = {"queue": queue_name, "run_id": run_id, "phase": phase_name}
    if labels:
        phase_labels.update(labels)

    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger.debug(f"Phase {phase_name} duration: {elapsed:.2f}s")
        event_capture.add_event(
            event_type="histogram",
            metric_name=f"{phase_name}_duration_seconds",
            value=elapsed,
            labels=phase_labels,
            status="success",
        )


@contextmanager
def record_run_duration(queue_name: str, run_id: str):
    """Context manager to record total run duration.

    Usage:
        with record_run_duration(queue, run):
            # do run work
            pass

    Args:
        queue_name: Name of the queue
        run_id: Unique run identifier
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger.debug(f"Run {run_id} duration: {elapsed:.2f}s")
        event_capture.add_event(
            event_type="histogram",
            metric_name="run_duration_seconds",
            value=elapsed,
            labels={"queue": queue_name, "run_id": run_id},
            status="success",
        )
