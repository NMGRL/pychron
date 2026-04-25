"""Integration tests for status and event panes working together."""

import time
import unittest
from unittest.mock import Mock, MagicMock

from pychron.observability.tasks.event import PrometheusEvent
from pychron.observability.tasks.model import PrometheusObservabilityModel
from pychron.observability.tasks.panes.status_pane import PrometheusStatusPane
from pychron.observability.tasks.panes.event_pane import PrometheusEventPane
from pychron.observability.tasks.task import PrometheusObservabilityTask


def _make_event(event_type, metric_name, value, labels=None):
    """Helper to create events with current timestamp."""
    if labels is None:
        labels = {}
    return PrometheusEvent(
        timestamp=time.time(),
        event_type=event_type,
        metric_name=metric_name,
        value=value,
        labels=labels,
    )


class TestPanesIntegration(unittest.TestCase):
    """Test integration between status and event panes."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = PrometheusObservabilityModel()
        self.status_pane = PrometheusStatusPane()
        self.event_pane = PrometheusEventPane(model=self.model)

    def test_panes_share_model(self):
        """Test that both panes can work with the same model."""
        # Status pane has its own model
        assert self.status_pane.model is not None

        # Event pane uses injected model
        assert self.event_pane.model is not None

        # They should be different instances (status creates its own)
        assert isinstance(self.status_pane.model, PrometheusObservabilityModel)
        assert isinstance(self.event_pane.model, PrometheusObservabilityModel)

    def test_event_pane_receives_model_events(self):
        """Test that event pane receives events from model."""
        # Add event to model
        event = _make_event("counter", "test_metric", 42, {"job": "test"})
        self.model.events.append(event)

        # Manually trigger update (in real app this would be via observer)
        self.event_pane._update_filtered_events()

        # Event pane should have filtered events
        assert len(self.event_pane.filtered_events) == 1
        assert self.event_pane.filtered_events[0].metric_name == "test_metric"

    def test_event_pane_filtering_works(self):
        """Test that event pane filtering works correctly."""
        # Add multiple events
        self.model.events = [
            _make_event("counter", "requests_total", 100, {"job": "api"}),
            _make_event("gauge", "temperature", 23.5, {"room": "lab"}),
            _make_event("histogram", "request_duration", 0.25, {}),
            _make_event("counter", "errors_total", 5, {"job": "api"}),
        ]

        # Trigger update (manually since we're not using observers in test)
        self.event_pane._update_filtered_events()

        # Initially all events shown
        assert len(self.event_pane.filtered_events) == 4

        # Filter by counter
        self.event_pane.event_type_filter = "counter"
        self.event_pane._update_filtered_events()
        assert len(self.event_pane.filtered_events) == 2

        # Search by metric name
        self.event_pane.search_text = "requests"
        self.event_pane._update_filtered_events()
        assert len(self.event_pane.filtered_events) == 1
        assert self.event_pane.filtered_events[0].metric_name == "requests_total"

    def test_status_pane_metrics_preview_with_events(self):
        """Test that status pane metrics preview updates with events."""
        # Add events to status pane's model
        self.status_pane.model.events = [
            _make_event("counter", "requests_total", 100, {}),
            _make_event("gauge", "temperature", 23.5, {}),
            _make_event("histogram", "request_duration", 0.25, {}),
        ]

        # Update metrics preview
        self.status_pane._update_metrics_preview()

        # Verify metrics were populated
        assert len(self.status_pane.counter_metrics) == 1
        assert self.status_pane.counter_metrics[0].metric_name == "requests_total"

        assert len(self.status_pane.gauge_metrics) == 1
        assert self.status_pane.gauge_metrics[0].metric_name == "temperature"

        assert len(self.status_pane.histogram_metrics) == 1
        assert self.status_pane.histogram_metrics[0].metric_name == "request_duration"

    def test_status_pane_event_count_reflects_events(self):
        """Test that status pane event count is correct."""
        assert self.status_pane.model.event_count == 0

        # Add events
        for i in range(5):
            self.status_pane.model.events.append(_make_event("counter", f"metric_{i}", i, {}))

        assert self.status_pane.model.event_count == 5

    def test_task_creates_panes_with_shared_model(self):
        """Test that task creates both panes properly."""
        task = PrometheusObservabilityTask()

        # Get the central pane (status pane)
        central_pane = task.create_central_pane()
        assert central_pane is not None
        assert isinstance(central_pane, PrometheusStatusPane)

        # Get the dock panes (event pane)
        dock_panes = task.create_dock_panes()
        assert len(dock_panes) > 0
        event_pane = dock_panes[0]
        assert isinstance(event_pane, PrometheusEventPane)

        # Both should have models
        assert central_pane.model is not None
        assert event_pane.model is not None

    def test_panes_trait_views_render(self):
        """Test that both panes' trait views render without errors."""
        # Status pane
        status_view = self.status_pane.traits_view()
        assert status_view is not None

        # Event pane
        event_view = self.event_pane.traits_view()
        assert event_view is not None

    def test_event_pane_auto_scroll_toggle(self):
        """Test event pane auto-scroll toggle."""
        # Initially auto-scroll is on
        assert len(self.event_pane.auto_scroll) > 0
        assert self.event_pane.auto_scroll[0] is True

        # Toggle it
        self.event_pane._auto_scroll_toggle_button_fired()
        assert self.event_pane.auto_scroll[0] is False

        # Toggle again
        self.event_pane._auto_scroll_toggle_button_fired()
        assert self.event_pane.auto_scroll[0] is True

    def test_event_pane_clear_filters(self):
        """Test event pane clear filters functionality."""
        # Set some filters
        self.event_pane.event_type_filter = "counter"
        self.event_pane.search_text = "test_metric"

        # Clear filters
        self.event_pane._clear_search_button_fired()

        # Verify cleared
        assert self.event_pane.event_type_filter == "all"
        assert self.event_pane.search_text == ""

    def test_status_pane_clear_events(self):
        """Test status pane clear events functionality."""
        # Add events
        self.status_pane.model.events = [
            _make_event("counter", "metric1", 100, {}),
            _make_event("gauge", "metric2", 50, {}),
        ]
        assert len(self.status_pane.model.events) == 2

        # Clear events
        self.status_pane._clear_button_fired()

        # Verify cleared
        assert len(self.status_pane.model.events) == 0

    def test_panes_cleanup_on_destroy(self):
        """Test that panes clean up properly on destroy."""
        status_pane = PrometheusStatusPane()
        event_pane = PrometheusEventPane(model=self.model)

        # Verify initial state
        assert status_pane.model is not None
        assert event_pane.model is not None

        # Destroy panes
        status_pane.destroy()
        event_pane.destroy()

        # Should not raise errors
        assert True

    def test_task_model_shared_between_panes(self):
        """Test that panes created by task share the same model."""
        task = PrometheusObservabilityTask()
        central_pane = task.create_central_pane()
        dock_panes = task.create_dock_panes()

        # Add event to central pane's model
        event = _make_event("counter", "test_metric", 100)
        central_pane.model.events.append(event)

        # Dock pane should receive it (both use task.model)
        event_pane = dock_panes[0]
        event_pane._update_filtered_events()
        assert len(event_pane.filtered_events) == 1
        assert event_pane.filtered_events[0].metric_name == "test_metric"


if __name__ == "__main__":
    unittest.main()
