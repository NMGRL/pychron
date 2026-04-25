"""Integration tests for live event capture.

Tests that verify the observability system correctly captures and displays
events through the UI components.

Note: These tests use event_capture.add_event() directly to simulate metric
operations. In production, these events would be triggered by actual metric
operations throughout Pychron.
"""

import time
import unittest
from unittest.mock import Mock, patch

from pychron.observability import event_capture
from pychron.observability.tasks.event import PrometheusEvent
from pychron.observability.tasks.model import PrometheusObservabilityModel
from pychron.observability.tasks.panes.status_pane import PrometheusStatusPane


class TestLiveEventCapture(unittest.TestCase):
    """Test event capture with simulated metric operations."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing events
        event_capture.clear_events()

        # Create model and pane
        self.model = PrometheusObservabilityModel()
        self.pane = PrometheusStatusPane(model=self.model)

    def tearDown(self):
        """Clean up after tests."""
        event_capture.clear_events()

    def test_counter_event_is_captured(self):
        """Test that simulating a counter operation creates an event."""
        # Get initial event count
        initial_count = len(self.model.events)

        # Simulate a counter increment via event_capture
        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
            labels=None,
            status="success",
        )

        # Give time for event to propagate through observer
        time.sleep(0.1)

        # Verify event was captured
        self.assertEqual(len(self.model.events), initial_count + 1)

        # Verify event details
        event = self.model.events[-1]
        self.assertIsInstance(event, PrometheusEvent)
        self.assertEqual(event.metric_name, "test_counter")
        self.assertEqual(event.event_type, "counter")
        self.assertEqual(event.value, 1.0)
        self.assertEqual(event.status, "success")

    def test_gauge_event_is_captured(self):
        """Test that simulating a gauge set creates an event."""
        initial_count = len(self.model.events)

        # Simulate a gauge set via event_capture
        event_capture.add_event(
            event_type="gauge",
            metric_name="test_gauge",
            value=42.5,
            labels=None,
            status="success",
        )

        time.sleep(0.1)

        # Verify event was captured
        self.assertEqual(len(self.model.events), initial_count + 1)

        # Verify event details
        event = self.model.events[-1]
        self.assertEqual(event.metric_name, "test_gauge")
        self.assertEqual(event.event_type, "gauge")
        self.assertEqual(event.value, 42.5)
        self.assertEqual(event.status, "success")

    def test_multiple_events_in_sequence(self):
        """Test that multiple event operations create multiple events."""
        initial_count = len(self.model.events)

        # Trigger multiple operations
        event_capture.add_event("counter", "counter_1", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("counter", "counter_2", 2.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "gauge_1", 100.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "gauge_2", 200.0, labels=None, status="success")

        time.sleep(0.1)

        # Verify all events were captured
        self.assertEqual(len(self.model.events), initial_count + 4)

        # Verify sequence
        events = self.model.events[-4:]
        self.assertEqual(events[0].metric_name, "counter_1")
        self.assertEqual(events[1].metric_name, "counter_2")
        self.assertEqual(events[2].metric_name, "gauge_1")
        self.assertEqual(events[3].metric_name, "gauge_2")

    def test_event_timestamps_are_recent(self):
        """Test that event timestamps are current."""
        before = time.time()

        event_capture.add_event("counter", "test_counter", 1.0, labels=None, status="success")

        time.sleep(0.1)

        after = time.time()

        event = self.model.events[-1]
        self.assertGreaterEqual(event.timestamp, before)
        self.assertLessEqual(event.timestamp, after)

    def test_event_count_property_updates(self):
        """Test that the model's event_count property updates."""
        initial_count = self.model.event_count

        # Trigger an event
        event_capture.add_event("counter", "test_counter", 1.0, labels=None, status="success")
        time.sleep(0.1)

        # Verify count increased
        self.assertEqual(self.model.event_count, initial_count + 1)

    def test_metrics_preview_updates_with_events(self):
        """Test that metrics preview updates when events occur."""
        # Trigger events
        event_capture.add_event("counter", "test_counter", 42.0, labels=None, status="success")
        time.sleep(0.1)
        event_capture.add_event("gauge", "test_gauge", 100.0, labels=None, status="success")
        time.sleep(0.1)

        # Get metrics preview
        preview = self.model.get_metrics_preview()

        # Verify preview contains the metrics
        self.assertIn("counter", preview)
        self.assertIn("gauge", preview)
        self.assertEqual(preview["counter"]["test_counter"], 42.0)
        self.assertEqual(preview["gauge"]["test_gauge"], 100.0)

    def test_pane_metrics_display_updates(self):
        """Test that pane display traits update with events."""
        # Trigger counter and gauge events
        event_capture.add_event("counter", "test_counter", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "test_gauge", 50.0, labels=None, status="success")
        time.sleep(0.1)

        # Trigger metrics preview update
        self.pane._update_metrics_preview()

        # Verify pane display lists are populated
        self.assertGreater(len(self.pane.counter_metrics), 0)
        self.assertGreater(len(self.pane.gauge_metrics), 0)

        # Verify contents
        counter_names = [m.metric_name for m in self.pane.counter_metrics]
        gauge_names = [m.metric_name for m in self.pane.gauge_metrics]
        self.assertIn("test_counter", counter_names)
        self.assertIn("test_gauge", gauge_names)

    def test_event_export_with_real_events(self):
        """Test that events can be exported."""
        # Trigger multiple events
        event_capture.add_event("counter", "counter_1", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "gauge_1", 100.0, labels=None, status="success")
        time.sleep(0.1)

        # Export as JSON
        json_data = self.model.export_events("json")
        self.assertIsInstance(json_data, str)
        self.assertIn("counter_1", json_data)
        self.assertIn("gauge_1", json_data)

        # Verify JSON is parseable
        import json

        data = json.loads(json_data)
        self.assertIn("events", data)
        self.assertGreater(len(data["events"]), 0)

        # Export as CSV
        csv_data = self.model.export_events("csv")
        self.assertIsInstance(csv_data, str)
        self.assertIn("counter_1", csv_data)
        self.assertIn("gauge_1", csv_data)

    def test_event_filtering_with_real_events(self):
        """Test that events can be filtered."""
        # Create mixed event types
        event_capture.add_event("counter", "my_counter", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "my_gauge", 100.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("counter", "my_counter", 2.0, labels=None, status="success")
        time.sleep(0.1)

        # Filter by type
        counter_events = self.model.get_filtered_events("counter")
        gauge_events = self.model.get_filtered_events("gauge")

        # Verify filtering
        self.assertGreater(len(counter_events), 0)
        self.assertGreater(len(gauge_events), 0)
        for event in counter_events:
            self.assertEqual(event.event_type, "counter")
        for event in gauge_events:
            self.assertEqual(event.event_type, "gauge")

    def test_event_capture_max_limit(self):
        """Test that event queue respects max size limit."""
        # Create many events (more than default max of 1000)
        for i in range(1010):
            event_capture.add_event(
                "counter",
                f"counter_{i}",
                float(i),
                labels=None,
                status="success",
            )

        time.sleep(0.5)

        # Verify queue respects max size
        self.assertLessEqual(len(self.model.events), 1000)


class TestEventPaneFiltering(unittest.TestCase):
    """Test event pane filtering with simulated events."""

    def setUp(self):
        """Set up test fixtures."""
        event_capture.clear_events()

        from pychron.observability.tasks.panes.event_pane import PrometheusEventPane

        self.model = PrometheusObservabilityModel()
        self.pane = PrometheusEventPane(model=self.model)

    def tearDown(self):
        """Clean up after tests."""
        event_capture.clear_events()

    def test_event_pane_receives_events(self):
        """Test that event pane receives events."""
        # Trigger events
        event_capture.add_event("counter", "pane_test_counter", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "pane_test_gauge", 50.0, labels=None, status="success")
        time.sleep(0.1)

        # Trigger filter update
        self.pane._update_filtered_events()

        # Verify pane sees events
        self.assertGreater(len(self.pane.filtered_events), 0)

    def test_event_pane_filtering_by_type(self):
        """Test that event pane can filter by type."""
        # Create mixed events
        event_capture.add_event("counter", "counter_1", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "gauge_1", 100.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("counter", "counter_2", 2.0, labels=None, status="success")
        time.sleep(0.1)

        # Filter by counter type
        self.pane.event_type_filter = "counter"
        self.pane._update_filtered_events()

        # Verify only counters shown
        self.assertGreater(len(self.pane.filtered_events), 0)
        for event in self.pane.filtered_events:
            self.assertEqual(event.event_type, "counter")

    def test_event_pane_search_filtering(self):
        """Test that event pane search works with events."""
        # Create events with specific names
        event_capture.add_event("counter", "database_queries", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("counter", "cache_hits", 1.0, labels=None, status="success")
        time.sleep(0.05)
        event_capture.add_event("gauge", "memory_usage", 500.0, labels=None, status="success")
        time.sleep(0.1)

        # Search for "database"
        self.pane.search_text = "database"
        self.pane._update_filtered_events()

        # Verify only database events shown
        self.assertGreater(len(self.pane.filtered_events), 0)
        for event in self.pane.filtered_events:
            self.assertIn("database", event.metric_name.lower())


if __name__ == "__main__":
    unittest.main()
