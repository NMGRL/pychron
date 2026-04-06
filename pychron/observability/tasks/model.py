"""Model for Prometheus observability UI.

Manages state for connection info, event history, and metrics display.
Binds to the Prometheus plugin and event capture system.
"""

import json
import logging
import threading
import time
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional

from traits.api import (
    Bool,
    Button,
    HasTraits,
    Int,
    List as TraitsList,
    Property,
    Str,
    observe,
)

from pychron.observability import event_capture
from pychron.observability.tasks.event import PrometheusEvent

logger = logging.getLogger(__name__)


class PrometheusObservabilityModel(HasTraits):
    """Model for Prometheus observability UI state and data.

    Attributes:
        enabled: Whether metrics collection is currently enabled
        host: Metrics server host
        port: Metrics server port
        namespace: Metric name namespace prefix
        events: List of captured events (most recent last)
        event_count: Number of events in queue
    """

    # Connection information (synced from plugin)
    enabled = Bool(False, label="Metrics Enabled")
    host = Str("127.0.0.1", label="Host")
    port = Int(9109, label="Port")
    namespace = Str("pychron", label="Namespace")

    # Event history
    events = TraitsList(label="Events")
    event_count = Property(Int, observe="events")
    event_filter = Str("", label="Filter")

    # Metrics summary
    last_event_time = Property(Str, observe="events")
    metrics_url = Property(Str, observe="host, port")

    # Control buttons
    toggle_enabled_button = Button()
    export_button = Button()
    clear_button = Button()
    open_browser_button = Button()

    # Internal state
    _plugin_ref = None
    _event_callback_registered = False
    _lock = threading.Lock()

    def __init__(self, plugin=None, **kw):
        """Initialize model.

        Args:
            plugin: Reference to PrometheusPlugin instance (optional)
            **kw: Additional traits
        """
        super().__init__(**kw)
        self._plugin_ref = plugin

        # Connect to plugin if provided
        if plugin:
            self._connect_to_plugin()

        # Start capturing events
        self._start_event_capture()

    def _connect_to_plugin(self) -> None:
        """Connect model traits to plugin traits."""
        if not self._plugin_ref:
            return

        try:
            # Observe plugin traits
            self._plugin_ref.observe(self._on_plugin_enabled_changed, "enabled")
            self._plugin_ref.observe(self._on_plugin_host_changed, "host")
            self._plugin_ref.observe(self._on_plugin_port_changed, "port")
            self._plugin_ref.observe(self._on_plugin_namespace_changed, "namespace")

            # Set initial values from plugin
            self.enabled = self._plugin_ref.enabled
            self.host = self._plugin_ref.host
            self.port = self._plugin_ref.port
            self.namespace = self._plugin_ref.namespace

            logger.debug("Connected model to Prometheus plugin")
        except Exception as e:
            logger.warning(f"Error connecting to plugin: {e}")

    def _on_plugin_enabled_changed(self, event=None):
        """Handle plugin enabled state change."""
        if self._plugin_ref:
            self.enabled = self._plugin_ref.enabled

    def _on_plugin_host_changed(self, event=None):
        """Handle plugin host change."""
        if self._plugin_ref:
            self.host = self._plugin_ref.host

    def _on_plugin_port_changed(self, event=None):
        """Handle plugin port change."""
        if self._plugin_ref:
            self.port = self._plugin_ref.port

    def _on_plugin_namespace_changed(self, event=None):
        """Handle plugin namespace change."""
        if self._plugin_ref:
            self.namespace = self._plugin_ref.namespace

    def _start_event_capture(self) -> None:
        """Register callback for event capture."""
        if not self._event_callback_registered:
            event_capture.register_callback(self._on_event_captured)
            self._event_callback_registered = True
            logger.debug("Started event capture for observability UI")

    def _on_event_captured(self, event: PrometheusEvent) -> None:
        """Handle a new event from the capture system.

        Called when a metrics operation occurs.
        Thread-safe - events can come from any thread.
        """
        logger.debug(
            f"Event captured: {event.metric_name} (from thread: {threading.current_thread().name})"
        )

        try:
            with self._lock:
                # Append to the list
                self.events.append(event)
                logger.debug(f"Event added to model. Total events: {len(self.events)}")
                # Keep only recent events
                if len(self.events) > 1000:
                    self.events = self.events[-1000:]

                # Create a copy to trigger trait change notification
                # This is necessary because list.append() doesn't trigger observers
                events_copy = list(self.events)

            # Reassign OUTSIDE the lock to avoid potential deadlocks
            # This triggers the Traits observer system
            self.events = events_copy
            logger.debug("Event list reassigned to trigger observers")
        except Exception as e:
            logger.warning(f"Error capturing event: {e}")

    def _get_event_count(self) -> int:
        """Get number of events in queue."""
        return len(self.events)

    event_count = Property(Int, observe="events")

    def _get_metrics_url(self) -> str:
        """Generate metrics URL from host and port."""
        return f"http://{self.host}:{self.port}/metrics"

    metrics_url = Property(Str, observe="host, port")

    def _get_last_event_time(self) -> str:
        """Get formatted time of last event."""
        if not self.events:
            return "No events yet"

        last_event = self.events[-1]
        dt = datetime.fromtimestamp(last_event.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    last_event_time = Property(Str, observe="events")

    def get_filtered_events(
        self, event_type: Optional[str] = None, count: Optional[int] = None
    ) -> List[PrometheusEvent]:
        """Get filtered events.

        Args:
            event_type: Filter by event type ("counter", "gauge", "histogram")
            count: Maximum number of events to return (default: all)

        Returns:
            List of filtered events.
        """
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if count is not None:
            events = events[-count:]

        return events

    def export_events(self, format_type: str = "json") -> str:
        """Export events as JSON or CSV.

        Args:
            format_type: "json" or "csv"

        Returns:
            Formatted string of events.
        """
        if format_type == "json":
            return self._export_json()
        elif format_type == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unknown format: {format_type}")

    def _export_json(self) -> str:
        """Export events as JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "connection": {
                "enabled": self.enabled,
                "host": self.host,
                "port": self.port,
                "namespace": self.namespace,
                "metrics_url": self.metrics_url,
            },
            "events": [e.to_dict() for e in self.events],
        }
        return json.dumps(data, indent=2)

    def _export_csv(self) -> str:
        """Export events as CSV."""
        lines = [
            "Timestamp,EventType,MetricName,Value,Labels,Status",
        ]

        for event in self.events:
            timestamp = datetime.fromtimestamp(event.timestamp).isoformat()
            labels_str = ";".join(f"{k}={v}" for k, v in event.labels.items())
            lines.append(
                f"{timestamp},{event.event_type},{event.metric_name},"
                f'{event.value},"{labels_str}",{event.status}'
            )

        return "\n".join(lines)

    def clear_events(self) -> None:
        """Clear all events from the model and capture system."""
        self.events = []
        event_capture.clear_events()
        logger.info("Cleared all events")

    def get_status_summary(self) -> Dict:
        """Get a summary of current status.

        Returns:
            Dict with status information.
        """
        return {
            "enabled": self.enabled,
            "host": self.host,
            "port": self.port,
            "namespace": self.namespace,
            "metrics_url": self.metrics_url,
            "event_count": self.event_count,
            "last_event_time": self.last_event_time,
        }

    def get_metrics_preview(self) -> Dict[str, Dict]:
        """Get a preview of recent metrics by type.

        Returns most recent value for each unique metric_name within each event type.

        Returns:
            Dict mapping event_type -> {metric_name: value}
        """
        preview = {}

        # Group events by type and metric name
        metrics_by_type = {}
        for event in self.events:
            if event.event_type not in metrics_by_type:
                metrics_by_type[event.event_type] = {}

            # Keep only the most recent value for each metric
            metrics_by_type[event.event_type][event.metric_name] = event.value

        return metrics_by_type

    @observe("toggle_enabled_button")
    def _toggle_enabled_button_fired(self, event=None):
        """Handle toggle enabled button (no-op, pane handles logic)."""
        pass

    @observe("export_button")
    def _export_button_fired(self, event=None):
        """Handle export button (no-op, pane handles logic)."""
        pass

    @observe("clear_button")
    def _clear_button_fired(self, event=None):
        """Handle clear button (no-op, pane handles logic)."""
        pass

    @observe("open_browser_button")
    def _open_browser_button_fired(self, event=None):
        """Handle open browser button (no-op, pane handles logic)."""
        pass

    def destroy(self) -> None:
        """Clean up model resources."""
        if self._event_callback_registered:
            event_capture.unregister_callback(self._on_event_captured)
            self._event_callback_registered = False
