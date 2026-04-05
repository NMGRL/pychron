"""Metrics facade providing no-op-safe metric operations."""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Generator

from . import registry
from .config import MetricsConfig

logger = logging.getLogger(__name__)

_config: MetricsConfig | None = None
_config_lock = threading.Lock()
_init_errors_logged: set[str] = set()
_errors_lock = threading.Lock()


def configure(config: MetricsConfig) -> None:
    """Configure the metrics system.

    Thread-safe configuration update.

    Args:
        config: MetricsConfig instance.
    """
    global _config
    with _config_lock:
        _config = config


def get_config() -> MetricsConfig:
    """Get the current metrics configuration.

    Returns:
        The current MetricsConfig or a default (disabled) config.
    """
    global _config
    with _config_lock:
        if _config is None:
            _config = MetricsConfig(enabled=False)
        return _config


def is_enabled() -> bool:
    """Check if metrics collection is enabled.

    Returns:
        True if enabled, False otherwise.
    """
    return get_config().enabled


def _log_once(error_key: str, message: str) -> None:
    """Log an error message only once (thread-safe).

    Args:
        error_key: Unique key for this error class.
        message: Error message to log.
    """
    with _errors_lock:
        if error_key not in _init_errors_logged:
            logger.warning(message)
            _init_errors_logged.add(error_key)


def _validate_labels(
    labels: list[str] | None,
    labelvalues: dict[str, str] | None,
    metric_name: str,
) -> bool:
    """Validate that labels and labelvalues match.

    Args:
        labels: List of expected label names.
        labelvalues: Dict of provided label values.
        metric_name: Name of metric for error reporting.

    Returns:
        True if valid, False otherwise (error logged).
    """
    if not labels or not labelvalues:
        return True

    # Check that all provided labels are expected
    for key in labelvalues.keys():
        if key not in labels:
            _log_once(
                f"label_mismatch_{metric_name}",
                f"Metric {metric_name}: unexpected label '{key}'. " f"Expected labels: {labels}",
            )
            return False

    # Check that all expected labels are provided
    for expected_label in labels:
        if expected_label not in labelvalues:
            _log_once(
                f"label_missing_{metric_name}",
                f"Metric {metric_name}: missing expected label '{expected_label}'. "
                f"Provided labels: {list(labelvalues.keys())}",
            )
            return False

    return True


def inc_counter(
    name: str,
    description: str,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
) -> None:
    """Increment a counter metric.

    Args:
        name: Metric name (without namespace prefix).
        description: Metric description.
        labels: List of label names.
        labelvalues: Dict mapping label names to values.
    """
    if not is_enabled():
        return

    labelvalues = labelvalues or {}
    try:
        # Validate labels match labelvalues
        if not _validate_labels(labels, labelvalues, name):
            return

        full_name = f"{get_config().namespace}_{name}"
        labels = labels or []
        counter = registry.counter(full_name, description, labelnames=labels)
        if labelvalues:
            counter.labels(**labelvalues).inc()
        else:
            counter.inc()
    except Exception as e:
        _log_once(f"counter_{name}", f"Failed to increment counter {name}: {e}")


def set_gauge(
    name: str,
    description: str,
    value: float,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
) -> None:
    """Set a gauge metric to a specific value.

    Args:
        name: Metric name (without namespace prefix).
        description: Metric description.
        value: Value to set.
        labels: List of label names.
        labelvalues: Dict mapping label names to values.
    """
    if not is_enabled():
        return

    labelvalues = labelvalues or {}
    try:
        # Validate labels match labelvalues
        if not _validate_labels(labels, labelvalues, name):
            return

        full_name = f"{get_config().namespace}_{name}"
        labels = labels or []
        gauge = registry.gauge(full_name, description, labelnames=labels)
        if labelvalues:
            gauge.labels(**labelvalues).set(value)
        else:
            gauge.set(value)
    except Exception as e:
        _log_once(f"gauge_{name}", f"Failed to set gauge {name}: {e}")


def observe_histogram(
    name: str,
    description: str,
    value: float,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
    buckets: tuple[float, ...] | None = None,
) -> None:
    """Observe a value in a histogram metric.

    Args:
        name: Metric name (without namespace prefix).
        description: Metric description.
        value: Value to observe.
        labels: List of label names.
        labelvalues: Dict mapping label names to values.
        buckets: Optional custom bucket boundaries.
    """
    if not is_enabled():
        return

    labelvalues = labelvalues or {}
    try:
        # Validate labels match labelvalues
        if not _validate_labels(labels, labelvalues, name):
            return

        full_name = f"{get_config().namespace}_{name}"
        labels = labels or []
        hist = registry.histogram(
            full_name,
            description,
            labelnames=labels,
            buckets=buckets,
        )
        if labelvalues:
            hist.labels(**labelvalues).observe(value)
        else:
            hist.observe(value)
    except Exception as e:
        _log_once(f"histogram_{name}", f"Failed to observe histogram {name}: {e}")


@contextmanager
def observe_duration(
    name: str,
    description: str,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
    buckets: tuple[float, ...] | None = None,
) -> Generator[None, None, None]:
    """Context manager to measure and observe operation duration.

    Args:
        name: Metric name (without namespace prefix).
        description: Metric description.
        labels: List of label names.
        labelvalues: Dict mapping label names to values.
        buckets: Optional custom bucket boundaries.

    Yields:
        Control to the context.
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        observe_histogram(
            name,
            description,
            elapsed,
            labels=labels,
            labelvalues=labelvalues,
            buckets=buckets,
        )
