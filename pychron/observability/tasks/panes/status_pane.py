"""Status pane for Prometheus observability task.

Displays connection information, controls, and tabs for metrics/events overview.
"""

import logging
import webbrowser
from datetime import datetime

from pyface.action.api import Action
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import (
    Dict,
    HasTraits,
    Instance,
    Int,
    List as TraitsList,
    Str,
    Button,
    observe,
)
from traitsui.api import (
    HGroup,
    Item,
    TabularEditor,
    UItem,
    UReadonly,
    VGroup,
    View,
)
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.observability.event_exporter import EventExporter
from pychron.observability.tasks.model import PrometheusObservabilityModel

logger = logging.getLogger(__name__)


class EventAdapter(TabularAdapter):
    """Adapter for displaying events in a table."""

    columns = [
        ("Timestamp", "timestamp_str"),
        ("Type", "event_type"),
        ("Metric", "metric_name"),
        ("Value", "value_str"),
        ("Status", "status"),
    ]

    timestamp_str = property(
        lambda self: datetime.fromtimestamp(self.item.timestamp).strftime("%H:%M:%S")
    )
    value_str = property(lambda self: str(self.item.value))
    timestamp_str_alignment = "left"
    event_type_alignment = "left"
    metric_name_alignment = "left"
    value_str_alignment = "right"
    status_alignment = "left"


class _MetricItem(HasTraits):
    """Simple wrapper for metrics display."""

    metric_name = Str()
    value = Str()

    def __init__(self, name, value, **kw):
        super().__init__(**kw)
        self.metric_name = name
        self.value = str(value)


class MetricsAdapter(TabularAdapter):
    """Adapter for displaying metrics in a table."""

    columns = [("Metric", "metric_name"), ("Value", "value")]

    metric_name_alignment = "left"
    value_alignment = "right"


class PrometheusStatusPane(TraitsTaskPane):
    """Central pane for Prometheus observability task.

    Displays:
    - Connection status and configuration
    - Control buttons
    - Tabbed view with connection details, recent events, and metrics
    """

    id = "pychron.observability.status_pane"
    name = "Status"

    # Proxy button traits - these forward to model buttons
    toggle_enabled_button = Button()
    export_button = Button()
    clear_button = Button()
    open_browser_button = Button()

    # Metrics preview display
    counter_metrics = TraitsList(label="Counters")
    gauge_metrics = TraitsList(label="Gauges")
    histogram_metrics = TraitsList(label="Histograms")

    # Internal model for observability
    model = Instance(PrometheusObservabilityModel)

    def __init__(self, model=None, **kw):
        """Initialize status pane with model."""
        super().__init__(**kw)
        self.model = model if model is not None else PrometheusObservabilityModel()
        # Listen for event changes to update metrics preview
        self.model.observe(self._on_model_events_changed, "events")

        # Also register directly with event_capture to handle background thread updates
        # The Traits observer doesn't work reliably from background threads
        from pychron.observability import event_capture

        event_capture.register_callback(self._on_event_capture_event)

    def trait_context(self):
        """Provide pane traits to the view context.

        This ensures TraitsUI resolves trait references (like 'counter_metrics',
        'host', etc.) on the pane object, not on the model.
        """
        return {"object": self}

    @property
    def host(self):
        """Proxy to model.host."""
        return self.model.host if self.model else ""

    @property
    def port(self):
        """Proxy to model.port."""
        return self.model.port if self.model else ""

    @property
    def namespace(self):
        """Proxy to model.namespace."""
        return self.model.namespace if self.model else ""

    @property
    def metrics_url(self):
        """Proxy to model.metrics_url."""
        return self.model.metrics_url if self.model else ""

    @property
    def enabled(self):
        """Proxy to model.enabled."""
        return self.model.enabled if self.model else False

    @property
    def event_count(self):
        """Proxy to model.event_count."""
        return self.model.event_count if self.model else 0

    @property
    def last_event_time(self):
        """Proxy to model.last_event_time."""
        return self.model.last_event_time if self.model else ""

    @property
    def events(self):
        """Proxy to model.events."""
        return self.model.events if self.model else []

    def traits_view(self):
        """Build the view for the status pane."""
        # Connection info section
        connection_group = VGroup(
            UReadonly("host", label="Host"),
            UReadonly("port", label="Port"),
            UReadonly("namespace", label="Namespace"),
            UReadonly("metrics_url", label="Metrics URL"),
            UReadonly(
                "enabled",
                label="Enabled",
            ),
            show_border=True,
            label="Connection Information",
        )

        # Control buttons
        controls_group = HGroup(
            icon_button_editor(
                "toggle_enabled_button",
                "start",
                tooltip="Toggle metrics collection",
            ),
            icon_button_editor(
                "export_button",
                "document_export",
                tooltip="Export events",
            ),
            icon_button_editor(
                "clear_button",
                "delete_no_confirm",
                tooltip="Clear all events",
            ),
            icon_button_editor(
                "open_browser_button",
                "link",
                tooltip="Open Prometheus in browser",
            ),
            show_border=True,
            label="Controls",
        )

        # Recent events section
        recent_events_group = VGroup(
            UReadonly("event_count", label="Total Events"),
            UReadonly("last_event_time", label="Last Event"),
            UItem(
                "events",
                editor=TabularEditor(adapter=EventAdapter(), editable=False),
                height=150,
            ),
            show_border=True,
            label="Recent Events",
        )

        # Metrics preview section
        metrics_preview_group = VGroup(
            HGroup(
                VGroup(
                    UItem(
                        "counter_metrics",
                        editor=TabularEditor(adapter=MetricsAdapter(), editable=False),
                        height=100,
                    ),
                    show_border=True,
                    label="Counters",
                ),
                VGroup(
                    UItem(
                        "gauge_metrics",
                        editor=TabularEditor(adapter=MetricsAdapter(), editable=False),
                        height=100,
                    ),
                    show_border=True,
                    label="Gauges",
                ),
                VGroup(
                    UItem(
                        "histogram_metrics",
                        editor=TabularEditor(adapter=MetricsAdapter(), editable=False),
                        height=100,
                    ),
                    show_border=True,
                    label="Histograms",
                ),
            ),
            show_border=True,
            label="Live Metrics Preview",
        )

        v = View(
            VGroup(
                connection_group,
                controls_group,
                recent_events_group,
                metrics_preview_group,
            ),
        )
        return v

    @observe("toggle_enabled_button")
    def _toggle_enabled_button_fired(self, event=None):
        """Toggle metrics collection."""
        if self.model and self.model._plugin_ref:
            self.model._plugin_ref.enabled = not self.model._plugin_ref.enabled
            logger.info(f"Toggled metrics enabled to {self.model.enabled}")

    @observe("export_button")
    def _export_button_fired(self, event=None):
        """Export events."""
        if not self.model.events:
            logger.warning("No events to export")
            return

        # Try to export as JSON first
        try:
            events_data = self.model.export_events("json")
            filepath = EventExporter.open_export_dialog(events_data, "json")
            if filepath:
                message = EventExporter.get_export_summary(self.model.event_count, filepath)
                logger.info(message)
            else:
                logger.info("Export cancelled")
        except Exception as e:
            logger.error(f"Export failed: {e}")

    @observe("clear_button")
    def _clear_button_fired(self, event=None):
        """Clear all events."""
        self.model.clear_events()
        logger.info("Cleared all events")

    @observe("open_browser_button")
    def _open_browser_button_fired(self, event=None):
        """Open Prometheus metrics in browser."""
        try:
            webbrowser.open(self.model.metrics_url)
            logger.info(f"Opened {self.model.metrics_url} in browser")
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")

    def _on_model_events_changed(self, event=None):
        """Handle model events change - update metrics preview."""
        self._update_metrics_preview()

    def _on_event_capture_event(self, event) -> None:
        """Handle events from event_capture system directly.

        Called from background thread when events are captured.
        Updates metrics preview to display real-time events.
        """
        # Update metrics preview whenever an event is captured
        # This provides real-time UI updates
        self._update_metrics_preview()

    def _update_metrics_preview(self):
        """Update the metrics preview from model."""
        metrics_preview = self.model.get_metrics_preview()

        # Convert to display format
        self.counter_metrics = [
            _MetricItem(name, value) for name, value in metrics_preview.get("counter", {}).items()
        ]
        self.gauge_metrics = [
            _MetricItem(name, value) for name, value in metrics_preview.get("gauge", {}).items()
        ]
        self.histogram_metrics = [
            _MetricItem(name, value) for name, value in metrics_preview.get("histogram", {}).items()
        ]

    def destroy(self):
        """Clean up pane resources."""
        # Unregister event capture callback
        try:
            from pychron.observability import event_capture

            event_capture.unregister_callback(self._on_event_capture_event)
        except Exception as e:
            logger.warning(f"Error unregistering event callback: {e}")

        if self.model:
            self.model.destroy()
        super().destroy()
