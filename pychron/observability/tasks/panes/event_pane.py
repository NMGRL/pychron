"""Event pane for Prometheus observability task.

Displays a detailed event log with filtering and search capabilities.
"""

import logging
from datetime import datetime

from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Button, List as TraitsList, Property, Str, observe
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
from pychron.observability.tasks.event import PrometheusEvent

logger = logging.getLogger(__name__)


class DetailedEventAdapter(TabularAdapter):
    """Adapter for displaying detailed events in a table."""

    columns = [
        ("Time", "timestamp_str"),
        ("Type", "event_type"),
        ("Metric", "metric_name"),
        ("Value", "value_str"),
        ("Labels", "labels_str"),
        ("Status", "status"),
    ]

    timestamp_str = property(
        lambda self: datetime.fromtimestamp(self.item.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    )
    value_str = property(lambda self: str(self.item.value))
    labels_str = property(
        lambda self: ", ".join(f"{k}={v}" for k, v in self.item.labels.items()) or "(none)"
    )

    timestamp_str_alignment = "left"
    event_type_alignment = "center"
    metric_name_alignment = "left"
    value_str_alignment = "right"
    labels_str_alignment = "left"
    status_alignment = "center"


class PrometheusEventPane(TraitsDockPane):
    """Dock pane for displaying and filtering Prometheus events.

    Features:
    - Scrollable event log with detailed columns
    - Filter by event type (counter, gauge, histogram, all)
    - Search by metric name
    - Auto-scroll toggle
    - Event count display
    """

    id = "pychron.observability.event_pane"
    name = "Event Log"

    # Event display and filtering
    filtered_events = TraitsList(label="Filtered Events")
    event_type_filter = Str("all", label="Event Type Filter")
    search_text = Str("", label="Search by Metric Name")
    auto_scroll = TraitsList([True], label="Auto Scroll")

    # Control buttons
    clear_search_button = Button()
    auto_scroll_toggle_button = Button()

    # Internal reference to model
    model = None

    def __init__(self, model=None, **kw):
        """Initialize event pane.

        Args:
            model: PrometheusObservabilityModel instance
        """
        super().__init__(**kw)
        self.model = model

        # Listen for model changes
        if self.model:
            self.model.observe(self._on_model_events_changed, "events")

    def trait_context(self):
        """Provide pane traits to the view context.

        This ensures TraitsUI resolves trait references (like 'event_type_filter',
        'search_text', etc.) on the pane object, not on the model.
        """
        return {"object": self}

    def _get_filtered_events_count(self) -> int:
        """Get count of filtered events."""
        return len(self.filtered_events)

    filtered_events_count = Property(observe="filtered_events")

    def _on_model_events_changed(self, event=None):
        """Handle model events list change."""
        self._update_filtered_events()

    def _update_filtered_events(self):
        """Update filtered events based on current filters."""
        if not self.model:
            self.filtered_events = []
            return

        events = self.model.events
        if not events:
            self.filtered_events = []
            return

        # Apply event type filter
        if self.event_type_filter != "all":
            events = [e for e in events if e.event_type == self.event_type_filter]

        # Apply search filter
        if self.search_text:
            search_lower = self.search_text.lower()
            events = [e for e in events if search_lower in e.metric_name.lower()]

        # Most recent events last (for display)
        self.filtered_events = events

    @observe("event_type_filter, search_text")
    def _on_filter_changed(self, event=None):
        """Handle filter changes."""
        self._update_filtered_events()

    @observe("clear_search_button")
    def _clear_search_button_fired(self, event=None):
        """Clear search text."""
        self.search_text = ""
        self.event_type_filter = "all"
        logger.info("Cleared all filters")

    @observe("auto_scroll_toggle_button")
    def _auto_scroll_toggle_button_fired(self, event=None):
        """Toggle auto-scroll."""
        is_auto_scroll = len(self.auto_scroll) > 0 and self.auto_scroll[0]
        self.auto_scroll = [not is_auto_scroll]
        logger.info(f"Auto-scroll toggled to {self.auto_scroll[0]}")

    def traits_view(self):
        """Build the view for the event pane."""
        # Filter controls
        filter_group = HGroup(
            Item(
                "event_type_filter",
                label="Type",
            ),
            Item(
                "search_text",
                label="Search",
            ),
            icon_button_editor(
                "clear_search_button",
                "delete_no_confirm",
                tooltip="Clear all filters",
            ),
            show_border=True,
            label="Filters",
        )

        # Auto-scroll toggle
        info_group = HGroup(
            UReadonly("filtered_events_count", label="Displayed Events"),
            icon_button_editor(
                "auto_scroll_toggle_button",
                "arrow_down",
                tooltip="Toggle auto-scroll to latest events",
            ),
            show_border=True,
            label="Controls",
        )

        # Event table
        events_group = VGroup(
            UItem(
                "filtered_events",
                editor=TabularEditor(adapter=DetailedEventAdapter(), editable=False),
                height=400,
            ),
            show_border=True,
            label="Event Details",
        )

        v = View(VGroup(filter_group, info_group, events_group))
        return v

    def destroy(self):
        """Clean up pane resources."""
        # Note: We don't unobserve because the model lifecycle is managed
        # by the task. Unobserving would prevent the event pane from
        # receiving updates if it's recreated.
        super().destroy()
