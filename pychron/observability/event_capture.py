"""Event capture system for Prometheus metrics operations.

This module intercepts metrics operations and logs them for UI display and export.
Designed to be low-overhead with async event capture.
"""

import logging
import threading
import time
from collections import deque
from typing import Callable, Dict, List, Optional

from .tasks.event import PrometheusEvent

logger = logging.getLogger(__name__)

# Global event queue (circular buffer, max 1000 events)
_event_queue: deque = deque(maxlen=1000)
_queue_lock = threading.Lock()

# Registered callbacks for event notifications
_event_callbacks: List[Callable[[PrometheusEvent], None]] = []
_callbacks_lock = threading.Lock()

# Whether event capture is enabled
_capture_enabled = True
_capture_lock = threading.Lock()


def add_event(
    event_type: str,
    metric_name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
    status: str = "success",
) -> None:
    """Add an event to the queue.

    Thread-safe. Should be called from any thread.

    Args:
        event_type: "counter", "gauge", or "histogram"
        metric_name: Full metric name
        value: Numeric value or delta
        labels: Optional dict of label names/values
        status: "success" or error message
    """
    if not _is_capture_enabled():
        logger.debug(f"Event capture disabled, ignoring event: {metric_name}")
        return

    event = PrometheusEvent(
        timestamp=time.time(),
        event_type=event_type,
        metric_name=metric_name,
        value=value,
        labels=labels or {},
        status=status,
    )

    logger.debug(f"Adding event to queue: {metric_name}, total callbacks: {len(_event_callbacks)}")

    # Add to queue (thread-safe via deque)
    with _queue_lock:
        _event_queue.append(event)
        logger.debug(f"Event queue size: {len(_event_queue)}")

    # Update Prometheus metrics registry
    _update_prometheus_metrics(event)

    # Notify callbacks (async, non-blocking)
    _notify_callbacks(event)


def get_events(count: Optional[int] = None) -> List[PrometheusEvent]:
    """Get recent events from the queue.

    Args:
        count: Number of most recent events to return.
               If None, returns all events.

    Returns:
        List of events, most recent last.
    """
    with _queue_lock:
        events = list(_event_queue)

    if count is not None:
        events = events[-count:]

    return events


def get_event_count() -> int:
    """Get current number of events in queue."""
    with _queue_lock:
        return len(_event_queue)


def clear_events() -> None:
    """Clear all events from the queue."""
    with _queue_lock:
        _event_queue.clear()


def set_capture_enabled(enabled: bool) -> None:
    """Enable or disable event capture."""
    global _capture_enabled
    with _capture_lock:
        _capture_enabled = enabled
        if enabled:
            logger.debug("Event capture enabled")
        else:
            logger.debug("Event capture disabled")


def _is_capture_enabled() -> bool:
    """Check if event capture is currently enabled."""
    with _capture_lock:
        return _capture_enabled


def register_callback(callback: Callable[[PrometheusEvent], None]) -> None:
    """Register a callback to be called when events occur.

    Callbacks are called asynchronously (in thread pool).
    Callbacks should be fast and non-blocking.

    Args:
        callback: Function taking PrometheusEvent as argument.
    """
    with _callbacks_lock:
        if callback not in _event_callbacks:
            _event_callbacks.append(callback)


def unregister_callback(callback: Callable[[PrometheusEvent], None]) -> None:
    """Unregister an event callback."""
    with _callbacks_lock:
        if callback in _event_callbacks:
            _event_callbacks.remove(callback)


def _notify_callbacks(event: PrometheusEvent) -> None:
    """Notify all registered callbacks of an event.

    Callbacks are called in a background thread pool to avoid blocking
    the metrics operation.
    """
    with _callbacks_lock:
        callbacks = _event_callbacks.copy()

    logger.debug(f"Notifying {len(callbacks)} callbacks for event: {event.metric_name}")

    # Call callbacks in background to avoid blocking
    for callback in callbacks:
        try:
            # Try to call in background thread if available
            # Otherwise call synchronously
            def _call_callback():
                logger.debug(f"Calling callback from thread: {threading.current_thread().name}")
                callback(event)

            threading.Thread(target=_call_callback, daemon=True).start()
        except Exception as e:
            logger.warning(f"Error calling event callback: {e}")


def _update_prometheus_metrics(event: PrometheusEvent) -> None:
    """Update Prometheus metrics registry based on captured event.

    Routes the event to the appropriate metrics function (counter, gauge, histogram)
    to update the Prometheus registry so metrics appear in /metrics endpoint.

    Args:
        event: PrometheusEvent to process
    """
    try:
        # Import metrics functions locally to avoid circular imports
        from . import metrics

        # Skip if metrics are disabled
        if not metrics.is_enabled():
            return

        # Convert label names to a list for metrics functions
        label_names = list(event.labels.keys()) if event.labels else None

        if event.event_type == "counter":
            metrics.inc_counter(
                name=event.metric_name,
                description=f"Counter for {event.metric_name}",
                labels=label_names,
                labelvalues=event.labels,
            )
            logger.debug(f"Updated counter metric: {event.metric_name}")

        elif event.event_type == "gauge":
            metrics.set_gauge(
                name=event.metric_name,
                description=f"Gauge for {event.metric_name}",
                value=event.value,
                labels=label_names,
                labelvalues=event.labels,
            )
            logger.debug(f"Updated gauge metric: {event.metric_name}")

        elif event.event_type == "histogram":
            metrics.observe_histogram(
                name=event.metric_name,
                description=f"Histogram for {event.metric_name}",
                value=event.value,
                labels=label_names,
                labelvalues=event.labels,
            )
            logger.debug(f"Updated histogram metric: {event.metric_name}")

    except Exception as e:
        logger.warning(f"Error updating Prometheus metrics for event {event.metric_name}: {e}")
