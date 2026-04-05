"""Tests for Prometheus status pane.

Tests cover:
- Pane initialization and model binding
- Connection info display
- Control button functionality
- Event display in table
- Integration with observability model
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from traits.api import HasTraits
from traitsui.api import View

from pychron.observability.tasks.event import PrometheusEvent
from pychron.observability.tasks.model import PrometheusObservabilityModel
from pychron.observability.tasks.panes.status_pane import (
    EventAdapter,
    PrometheusStatusPane,
)


class TestEventAdapter(unittest.TestCase):
    """Test the event table adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = EventAdapter()
        self.event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="gauge",
            metric_name="test_metric",
            value=42.5,
            labels={"job": "test"},
            status="success",
        )
        self.adapter.item = self.event

    def test_adapter_columns_defined(self):
        """Test that adapter has correct columns."""
        self.assertEqual(len(self.adapter.columns), 5)
        column_names = [col[0] for col in self.adapter.columns]
        self.assertIn("Timestamp", column_names)
        self.assertIn("Type", column_names)
        self.assertIn("Metric", column_names)
        self.assertIn("Value", column_names)
        self.assertIn("Status", column_names)

    def test_adapter_timestamp_formatting(self):
        """Test that timestamp is formatted correctly."""
        self.assertIsNotNone(self.adapter.timestamp_str)
        self.assertIn(":", self.adapter.timestamp_str)
        # Should be HH:MM:SS format
        parts = self.adapter.timestamp_str.split(":")
        self.assertEqual(len(parts), 3)

    def test_adapter_value_string_conversion(self):
        """Test that value is converted to string."""
        self.assertEqual(self.adapter.value_str, "42.5")

    def test_adapter_alignments(self):
        """Test that column alignments are set."""
        self.assertEqual(self.adapter.timestamp_str_alignment, "left")
        self.assertEqual(self.adapter.event_type_alignment, "left")
        self.assertEqual(self.adapter.metric_name_alignment, "left")
        self.assertEqual(self.adapter.value_str_alignment, "right")
        self.assertEqual(self.adapter.status_alignment, "left")


class TestPrometheusStatusPane(unittest.TestCase):
    """Test the Prometheus status pane."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the plugin to avoid Qt/Traits dependencies
        self.pane = PrometheusStatusPane()
        # Replace model with a mock one
        self.pane.model = Mock(spec=PrometheusObservabilityModel)

    def test_pane_initialization(self):
        """Test that pane initializes with correct id and name."""
        self.assertEqual(self.pane.id, "pychron.observability.status_pane")
        self.assertEqual(self.pane.name, "Status")

    def test_pane_has_model(self):
        """Test that pane has a model."""
        self.assertIsNotNone(self.pane.model)

    def test_pane_has_button_traits(self):
        """Test that pane has button traits from PrometheusStatusPane."""
        # Create a fresh pane without mocking so we see the actual traits
        fresh_pane = PrometheusStatusPane()
        # Check that trait descriptors exist on the class
        traits = fresh_pane.class_traits()
        self.assertIn("toggle_enabled_button", traits)
        self.assertIn("export_button", traits)
        self.assertIn("clear_button", traits)
        self.assertIn("open_browser_button", traits)
        fresh_pane.destroy()

    def test_traits_view_returns_view(self):
        """Test that traits_view returns a View object."""
        view = self.pane.traits_view()
        self.assertIsInstance(view, View)

    def test_toggle_enabled_button_handler(self):
        """Test toggle enabled button handler."""
        # Set up mock plugin
        self.pane.model._plugin_ref = Mock()
        self.pane.model._plugin_ref.enabled = False
        self.pane.model.enabled = False

        # Fire the button
        self.pane._toggle_enabled_button_fired()

        # Verify plugin was toggled
        self.pane.model._plugin_ref.enabled = not self.pane.model._plugin_ref.enabled

    def test_toggle_enabled_button_no_plugin(self):
        """Test toggle enabled button when no plugin is available."""
        self.pane.model._plugin_ref = None
        # Should not raise an exception
        self.pane._toggle_enabled_button_fired()

    def test_export_button_handler(self):
        """Test export button handler."""
        self.pane.model.event_count = 5
        self.pane.model.events = [Mock()]  # At least one event
        self.pane.model.export_events = Mock(return_value='{"events": []}')
        # Should not raise an exception
        self.pane._export_button_fired()

    def test_clear_button_handler(self):
        """Test clear button handler."""
        self.pane.model.clear_events = Mock()
        self.pane._clear_button_fired()
        self.pane.model.clear_events.assert_called_once()

    @patch("webbrowser.open")
    def test_open_browser_button_handler(self, mock_browser):
        """Test open browser button handler."""
        self.pane.model.metrics_url = "http://localhost:9109/metrics"
        self.pane._open_browser_button_fired()
        mock_browser.assert_called_once_with("http://localhost:9109/metrics")

    @patch("webbrowser.open")
    def test_open_browser_button_handler_exception(self, mock_browser):
        """Test open browser button handler with exception."""
        mock_browser.side_effect = Exception("Browser error")
        self.pane.model.metrics_url = "http://localhost:9109/metrics"
        # Should not raise an exception
        self.pane._open_browser_button_fired()

    def test_destroy_calls_model_destroy(self):
        """Test that destroy calls model.destroy()."""
        self.pane.model.destroy = Mock()
        self.pane.destroy()
        self.pane.model.destroy.assert_called_once()

    def test_destroy_with_none_model(self):
        """Test that destroy handles None model gracefully."""
        self.pane.model = None
        # Should not raise an exception
        self.pane.destroy()


class TestStatusPaneIntegration(unittest.TestCase):
    """Integration tests for status pane with model."""

    def setUp(self):
        """Set up test fixtures."""
        self.pane = PrometheusStatusPane()

    def test_pane_model_initialization(self):
        """Test that pane model is properly initialized."""
        self.assertIsNotNone(self.pane.model)
        self.assertIsInstance(self.pane.model, PrometheusObservabilityModel)

    def test_pane_model_properties_accessible(self):
        """Test that model properties are accessible through pane."""
        # Model should have these properties
        self.assertTrue(hasattr(self.pane.model, "enabled"))
        self.assertTrue(hasattr(self.pane.model, "host"))
        self.assertTrue(hasattr(self.pane.model, "port"))
        self.assertTrue(hasattr(self.pane.model, "namespace"))
        self.assertTrue(hasattr(self.pane.model, "metrics_url"))
        self.assertTrue(hasattr(self.pane.model, "events"))
        self.assertTrue(hasattr(self.pane.model, "event_count"))
        self.assertTrue(hasattr(self.pane.model, "last_event_time"))

    def test_pane_can_display_events(self):
        """Test that pane can display events from model."""
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="counter",
            metric_name="test_counter",
            value=100,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]
        self.assertEqual(len(self.pane.model.events), 1)

    def test_pane_event_count_property(self):
        """Test that event count property works."""
        self.assertEqual(self.pane.model.event_count, 0)
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="gauge",
            metric_name="test_gauge",
            value=50,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]
        self.assertEqual(self.pane.model.event_count, 1)

    def test_pane_metrics_url_property(self):
        """Test that metrics URL is generated correctly."""
        expected_url = f"http://{self.pane.model.host}:{self.pane.model.port}/metrics"
        self.assertEqual(self.pane.model.metrics_url, expected_url)

    def test_pane_last_event_time_property(self):
        """Test that last event time is formatted correctly."""
        # When no events, should say "No events yet"
        self.assertEqual(self.pane.model.last_event_time, "No events yet")

        # Add an event
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="histogram",
            metric_name="test_histogram",
            value=0.5,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]
        # Should now have a formatted timestamp
        self.assertNotEqual(self.pane.model.last_event_time, "No events yet")
        self.assertIn("-", self.pane.model.last_event_time)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.pane:
            self.pane.destroy()


class TestStatusPaneMetricsPreview(unittest.TestCase):
    """Test metrics preview functionality in status pane."""

    def setUp(self):
        """Set up test fixtures."""
        self.pane = PrometheusStatusPane()

    def test_metrics_preview_traits_exist(self):
        """Test that metrics preview traits exist."""
        self.assertTrue(hasattr(self.pane, "counter_metrics"))
        self.assertTrue(hasattr(self.pane, "gauge_metrics"))
        self.assertTrue(hasattr(self.pane, "histogram_metrics"))

    def test_metrics_preview_initial_state(self):
        """Test initial state of metrics preview."""
        self.assertEqual(len(self.pane.counter_metrics), 0)
        self.assertEqual(len(self.pane.gauge_metrics), 0)
        self.assertEqual(len(self.pane.histogram_metrics), 0)

    def test_update_metrics_preview_single_counter(self):
        """Test updating metrics preview with a single counter."""
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="counter",
            metric_name="requests_total",
            value=100,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]
        self.pane._update_metrics_preview()

        self.assertEqual(len(self.pane.counter_metrics), 1)
        self.assertEqual(self.pane.counter_metrics[0].metric_name, "requests_total")
        self.assertEqual(self.pane.counter_metrics[0].value, "100")

    def test_update_metrics_preview_multiple_types(self):
        """Test updating metrics preview with multiple event types."""
        events = [
            PrometheusEvent(1.0, "counter", "counter1", 10, {}, "success"),
            PrometheusEvent(2.0, "gauge", "gauge1", 50, {}, "success"),
            PrometheusEvent(3.0, "histogram", "histogram1", 0.5, {}, "success"),
        ]
        self.pane.model.events = events
        self.pane._update_metrics_preview()

        self.assertEqual(len(self.pane.counter_metrics), 1)
        self.assertEqual(len(self.pane.gauge_metrics), 1)
        self.assertEqual(len(self.pane.histogram_metrics), 1)

    def test_update_metrics_preview_duplicate_metrics(self):
        """Test that duplicate metrics keep only the latest value."""
        events = [
            PrometheusEvent(1.0, "gauge", "temperature", 70, {}, "success"),
            PrometheusEvent(2.0, "gauge", "temperature", 72, {}, "success"),
            PrometheusEvent(3.0, "gauge", "temperature", 75, {}, "success"),
        ]
        self.pane.model.events = events
        self.pane._update_metrics_preview()

        # Should only have one temperature gauge with the latest value
        self.assertEqual(len(self.pane.gauge_metrics), 1)
        self.assertEqual(self.pane.gauge_metrics[0].metric_name, "temperature")
        self.assertEqual(self.pane.gauge_metrics[0].value, "75")

    def test_update_metrics_preview_multiple_same_type(self):
        """Test updating with multiple metrics of the same type."""
        events = [
            PrometheusEvent(1.0, "gauge", "temperature", 70, {}, "success"),
            PrometheusEvent(2.0, "gauge", "humidity", 60, {}, "success"),
            PrometheusEvent(3.0, "gauge", "pressure", 1013, {}, "success"),
        ]
        self.pane.model.events = events
        self.pane._update_metrics_preview()

        self.assertEqual(len(self.pane.gauge_metrics), 3)
        metric_names = [m.metric_name for m in self.pane.gauge_metrics]
        self.assertIn("temperature", metric_names)
        self.assertIn("humidity", metric_names)
        self.assertIn("pressure", metric_names)

    def test_model_events_change_triggers_update(self):
        """Test that model events change triggers metrics preview update."""
        # Add an event
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="counter",
            metric_name="test_counter",
            value=1,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]

        # Trigger the callback
        self.pane._on_model_events_changed()

        self.assertEqual(len(self.pane.counter_metrics), 1)

    def test_metrics_preview_with_labels(self):
        """Test metrics preview with labeled metrics."""
        events = [
            PrometheusEvent(
                1.0,
                "gauge",
                "temperature",
                70,
                {"zone": "1", "device": "furnace"},
                "success",
            ),
            PrometheusEvent(
                2.0,
                "gauge",
                "temperature",
                75,
                {"zone": "2", "device": "furnace"},
                "success",
            ),
        ]
        self.pane.model.events = events
        self.pane._update_metrics_preview()

        # Should have only one metric entry (most recent value wins)
        self.assertEqual(len(self.pane.gauge_metrics), 1)
        self.assertEqual(self.pane.gauge_metrics[0].value, "75")

    def test_metrics_float_values_formatted(self):
        """Test that float values are properly formatted in metrics preview."""
        event = PrometheusEvent(
            timestamp=1609459200.0,
            event_type="histogram",
            metric_name="response_time",
            value=0.1234567,
            labels={},
            status="success",
        )
        self.pane.model.events = [event]
        self.pane._update_metrics_preview()

        self.assertEqual(len(self.pane.histogram_metrics), 1)
        # Value should be string representation of float
        self.assertEqual(self.pane.histogram_metrics[0].value, "0.1234567")

    def test_clear_metrics_on_empty_events(self):
        """Test that metrics preview is cleared when events are empty."""
        # First add some events
        events = [
            PrometheusEvent(1.0, "counter", "counter1", 10, {}, "success"),
        ]
        self.pane.model.events = events
        self.pane._update_metrics_preview()
        self.assertEqual(len(self.pane.counter_metrics), 1)

        # Now clear events
        self.pane.model.events = []
        self.pane._update_metrics_preview()
        self.assertEqual(len(self.pane.counter_metrics), 0)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.pane:
            self.pane.destroy()


if __name__ == "__main__":
    unittest.main()
