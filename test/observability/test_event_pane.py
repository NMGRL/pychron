"""Tests for Prometheus event pane.

Tests cover:
- Event pane initialization and model binding
- Event filtering by type
- Search by metric name
- Auto-scroll toggle
- Event count display
- Table display with proper formatting
"""

import unittest
from unittest.mock import Mock, patch

from traits.api import HasTraits

from pychron.observability.tasks.event import PrometheusEvent
from pychron.observability.tasks.model import PrometheusObservabilityModel
from pychron.observability.tasks.panes.event_pane import (
    DetailedEventAdapter,
    PrometheusEventPane,
)


class TestDetailedEventAdapter(unittest.TestCase):
    """Test the detailed event table adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = DetailedEventAdapter()
        self.event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="gauge",
            metric_name="temperature_celsius",
            value=72.5,
            labels={"device": "furnace", "zone": "1"},
            status="success",
        )
        self.adapter.item = self.event

    def test_adapter_columns_defined(self):
        """Test that adapter has correct columns."""
        self.assertEqual(len(self.adapter.columns), 6)
        column_names = [col[0] for col in self.adapter.columns]
        self.assertIn("Time", column_names)
        self.assertIn("Type", column_names)
        self.assertIn("Metric", column_names)
        self.assertIn("Value", column_names)
        self.assertIn("Labels", column_names)
        self.assertIn("Status", column_names)

    def test_adapter_timestamp_formatting(self):
        """Test that timestamp is formatted with full date and time."""
        self.assertIsNotNone(self.adapter.timestamp_str)
        # Should be YYYY-MM-DD HH:MM:SS format
        parts = self.adapter.timestamp_str.split(" ")
        self.assertEqual(len(parts), 2)
        # Date part
        self.assertIn("-", parts[0])
        # Time part
        self.assertIn(":", parts[1])

    def test_adapter_value_string_conversion(self):
        """Test that value is converted to string."""
        self.assertEqual(self.adapter.value_str, "72.5")

    def test_adapter_labels_formatting(self):
        """Test that labels are formatted correctly."""
        self.assertIn("device=furnace", self.adapter.labels_str)
        self.assertIn("zone=1", self.adapter.labels_str)
        self.assertIn(",", self.adapter.labels_str)

    def test_adapter_labels_empty(self):
        """Test labels formatting when empty."""
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="counter",
            metric_name="test",
            value=1,
            labels={},
            status="success",
        )
        self.adapter.item = event
        self.assertEqual(self.adapter.labels_str, "(none)")

    def test_adapter_alignments(self):
        """Test that column alignments are set."""
        self.assertEqual(self.adapter.timestamp_str_alignment, "left")
        self.assertEqual(self.adapter.event_type_alignment, "center")
        self.assertEqual(self.adapter.metric_name_alignment, "left")
        self.assertEqual(self.adapter.value_str_alignment, "right")
        self.assertEqual(self.adapter.labels_str_alignment, "left")
        self.assertEqual(self.adapter.status_alignment, "center")


class TestPrometheusEventPane(unittest.TestCase):
    """Test the Prometheus event pane."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = Mock(spec=PrometheusObservabilityModel)
        self.model.events = []
        self.pane = PrometheusEventPane(model=self.model)

    def test_pane_initialization(self):
        """Test that pane initializes with correct id and name."""
        self.assertEqual(self.pane.id, "pychron.observability.event_pane")
        self.assertEqual(self.pane.name, "Event Log")

    def test_pane_has_model(self):
        """Test that pane has a model."""
        self.assertIsNotNone(self.pane.model)
        self.assertEqual(self.pane.model, self.model)

    def test_pane_without_model(self):
        """Test that pane can be initialized without a model."""
        pane = PrometheusEventPane(model=None)
        self.assertIsNone(pane.model)

    def test_pane_has_filter_traits(self):
        """Test that pane has filtering traits."""
        self.assertTrue(hasattr(self.pane, "event_type_filter"))
        self.assertTrue(hasattr(self.pane, "search_text"))
        self.assertTrue(hasattr(self.pane, "filtered_events"))
        self.assertTrue(hasattr(self.pane, "auto_scroll"))

    def test_initial_filter_values(self):
        """Test initial filter values."""
        self.assertEqual(self.pane.event_type_filter, "all")
        self.assertEqual(self.pane.search_text, "")
        self.assertEqual(len(self.pane.auto_scroll), 1)
        self.assertTrue(self.pane.auto_scroll[0])

    def test_filter_by_event_type_counter(self):
        """Test filtering by counter type."""
        events = [
            PrometheusEvent(1.0, "counter", "counter1", 1, {}, "success"),
            PrometheusEvent(2.0, "gauge", "gauge1", 50, {}, "success"),
            PrometheusEvent(3.0, "counter", "counter2", 2, {}, "success"),
        ]
        self.model.events = events

        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 3)

        # Now filter to counter only
        self.pane.event_type_filter = "counter"
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 2)
        for event in self.pane.filtered_events:
            self.assertEqual(event.event_type, "counter")

    def test_filter_by_event_type_gauge(self):
        """Test filtering by gauge type."""
        events = [
            PrometheusEvent(1.0, "counter", "counter1", 1, {}, "success"),
            PrometheusEvent(2.0, "gauge", "gauge1", 50, {}, "success"),
            PrometheusEvent(3.0, "gauge", "gauge2", 60, {}, "success"),
        ]
        self.model.events = events

        self.pane.event_type_filter = "gauge"
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 2)
        for event in self.pane.filtered_events:
            self.assertEqual(event.event_type, "gauge")

    def test_search_by_metric_name(self):
        """Test searching by metric name."""
        events = [
            PrometheusEvent(1.0, "counter", "pychron_runs_started_total", 10, {}, "success"),
            PrometheusEvent(2.0, "gauge", "temperature_celsius", 72.5, {}, "success"),
            PrometheusEvent(3.0, "histogram", "pychron_timing_seconds", 0.5, {}, "success"),
        ]
        self.model.events = events

        self.pane.search_text = "pychron"
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 2)

    def test_search_case_insensitive(self):
        """Test that search is case insensitive."""
        events = [
            PrometheusEvent(1.0, "counter", "MyMetric", 1, {}, "success"),
            PrometheusEvent(2.0, "gauge", "other_metric", 50, {}, "success"),
        ]
        self.model.events = events

        self.pane.search_text = "mymetric"
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 1)

    def test_combined_filters(self):
        """Test combining event type and search filters."""
        events = [
            PrometheusEvent(1.0, "counter", "pychron_counter_total", 10, {}, "success"),
            PrometheusEvent(2.0, "counter", "other_counter_total", 20, {}, "success"),
            PrometheusEvent(3.0, "gauge", "pychron_gauge", 50, {}, "success"),
        ]
        self.model.events = events

        self.pane.event_type_filter = "counter"
        self.pane.search_text = "pychron"
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 1)
        self.assertEqual(self.pane.filtered_events[0].metric_name, "pychron_counter_total")

    def test_clear_search_button(self):
        """Test clear search button."""
        self.pane.event_type_filter = "gauge"
        self.pane.search_text = "test_search"
        self.pane._clear_search_button_fired()
        self.assertEqual(self.pane.search_text, "")
        self.assertEqual(self.pane.event_type_filter, "all")

    def test_auto_scroll_toggle_on(self):
        """Test toggling auto-scroll when it's on."""
        self.pane.auto_scroll = [True]
        self.pane._auto_scroll_toggle_button_fired()
        self.assertFalse(self.pane.auto_scroll[0])

    def test_auto_scroll_toggle_off(self):
        """Test toggling auto-scroll when it's off."""
        self.pane.auto_scroll = [False]
        self.pane._auto_scroll_toggle_button_fired()
        self.assertTrue(self.pane.auto_scroll[0])

    def test_filtered_events_count_property(self):
        """Test filtered events count property."""
        events = [
            PrometheusEvent(1.0, "counter", "metric1", 1, {}, "success"),
            PrometheusEvent(2.0, "gauge", "metric2", 50, {}, "success"),
        ]
        self.pane.filtered_events = events
        self.assertEqual(self.pane.filtered_events_count, 2)

    def test_model_events_change_updates_filtered(self):
        """Test that model events change updates filtered events."""
        events = [
            PrometheusEvent(1.0, "counter", "metric1", 1, {}, "success"),
        ]
        self.model.events = events
        self.pane._on_model_events_changed()
        self.assertEqual(len(self.pane.filtered_events), 1)

    def test_empty_model_events(self):
        """Test with empty model events."""
        self.model.events = []
        self.pane._update_filtered_events()
        self.assertEqual(len(self.pane.filtered_events), 0)

    def test_traits_view_returns_view(self):
        """Test that traits_view returns a View object."""
        from traitsui.api import View

        view = self.pane.traits_view()
        self.assertIsInstance(view, View)

    def test_destroy_unobserves_model(self):
        """Test that destroy handles model cleanup."""
        # The event pane doesn't unobserve since model lifecycle
        # is managed by the task
        self.pane.destroy()
        # Should not raise an exception

    def test_destroy_without_model(self):
        """Test destroy when model is None."""
        pane = PrometheusEventPane(model=None)
        # Should not raise an exception
        pane.destroy()


if __name__ == "__main__":
    unittest.main()
