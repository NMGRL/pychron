"""Tests for PrometheusObservabilityTask and PrometheusObservabilityModel."""

import time
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from traits.api import HasTraits, Bool, Int, Str

from pychron.observability import event_capture
from pychron.observability.tasks.event import PrometheusEvent
from pychron.observability.tasks.model import PrometheusObservabilityModel
from pychron.observability.tasks.task import PrometheusObservabilityTask


class TestPrometheusObservabilityTask(unittest.TestCase):
    """Tests for PrometheusObservabilityTask."""

    def setUp(self) -> None:
        """Set up test."""
        self.task = PrometheusObservabilityTask()

    def test_task_creation(self) -> None:
        """Test creating a task."""
        self.assertEqual(
            self.task.id,
            "pychron.observability.prometheus_task",
        )
        self.assertEqual(self.task.name, "Prometheus Observability")

    def test_task_window_size(self) -> None:
        """Test task window dimensions."""
        self.assertGreater(self.task.window_width, 0)
        self.assertGreater(self.task.window_height, 0)

    def test_create_central_pane(self) -> None:
        """Test creating central pane (will be fully tested when panes created)."""
        # Panes are created dynamically, so we just verify the method exists
        self.assertTrue(callable(self.task.create_central_pane))

    def test_create_dock_panes(self) -> None:
        """Test creating dock panes (will be fully tested when panes created)."""
        # Panes are created dynamically, so we just verify the method exists
        self.assertTrue(callable(self.task.create_dock_panes))


class TestPrometheusObservabilityModel(unittest.TestCase):
    """Tests for PrometheusObservabilityModel."""

    def setUp(self) -> None:
        """Set up test."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()
        self.model = PrometheusObservabilityModel()

    def tearDown(self) -> None:
        """Clean up."""
        if hasattr(self, "model"):
            self.model.destroy()
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def test_model_creation(self) -> None:
        """Test creating model."""
        self.assertFalse(self.model.enabled)
        self.assertEqual(self.model.host, "127.0.0.1")
        self.assertEqual(self.model.port, 9109)
        self.assertEqual(self.model.namespace, "pychron")

    def test_model_metrics_url(self) -> None:
        """Test metrics URL property."""
        url = self.model.metrics_url
        self.assertEqual(url, "http://127.0.0.1:9109/metrics")

    def test_model_metrics_url_updates(self) -> None:
        """Test that metrics URL updates when host/port change."""
        self.model.host = "0.0.0.0"
        self.assertEqual(self.model.metrics_url, "http://0.0.0.0:9109/metrics")

        self.model.port = 8888
        self.assertEqual(self.model.metrics_url, "http://0.0.0.0:8888/metrics")

    def test_event_count_property(self) -> None:
        """Test event count property."""
        self.assertEqual(self.model.event_count, 0)

        # Add event via event_capture
        event_capture.add_event("counter", "test", 1.0)
        time.sleep(0.1)

        self.assertGreater(self.model.event_count, 0)

    def test_last_event_time_property(self) -> None:
        """Test last event time property."""
        self.assertIn("No events", self.model.last_event_time)

        # Add an event
        event_capture.add_event("counter", "test", 1.0)
        time.sleep(0.1)

        self.assertNotIn("No events", self.model.last_event_time)

    def test_event_capture_integration(self) -> None:
        """Test that model captures events from event_capture."""
        # Add events
        event_capture.add_event("counter", "test_counter", 1.0)
        event_capture.add_event("gauge", "test_gauge", 42.0)
        time.sleep(0.2)

        self.assertEqual(self.model.event_count, 2)
        self.assertEqual(len(self.model.events), 2)

    def test_get_filtered_events(self) -> None:
        """Test filtering events by type."""
        # Add mixed events
        event_capture.add_event("counter", "counter_1", 1.0)
        event_capture.add_event("gauge", "gauge_1", 10.0)
        event_capture.add_event("counter", "counter_2", 2.0)
        time.sleep(0.2)

        counters = self.model.get_filtered_events(event_type="counter")
        self.assertEqual(len(counters), 2)
        self.assertTrue(all(e.event_type == "counter" for e in counters))

        gauges = self.model.get_filtered_events(event_type="gauge")
        self.assertEqual(len(gauges), 1)

    def test_get_filtered_events_with_count(self) -> None:
        """Test limiting number of filtered events."""
        # Add events
        for i in range(10):
            event_capture.add_event("counter", f"counter_{i}", float(i))
        time.sleep(0.2)

        # Get last 3 events
        events = self.model.get_filtered_events(
            event_type="counter",
            count=3,
        )
        self.assertEqual(len(events), 3)

    def test_export_events_json(self) -> None:
        """Test exporting events as JSON."""
        event_capture.add_event("counter", "test", 1.0)
        time.sleep(0.1)

        json_str = self.model.export_events(format_type="json")
        self.assertIn("counter", json_str)
        self.assertIn("test", json_str)
        self.assertIn("timestamp", json_str)
        self.assertIn("connection", json_str)

    def test_export_events_csv(self) -> None:
        """Test exporting events as CSV."""
        event_capture.add_event(
            "counter",
            "test_counter",
            1.0,
            labels={"device": "furnace"},
        )
        time.sleep(0.1)

        csv_str = self.model.export_events(format_type="csv")
        self.assertIn("Timestamp", csv_str)
        self.assertIn("EventType", csv_str)
        self.assertIn("counter", csv_str)
        self.assertIn("furnace", csv_str)

    def test_export_unknown_format_raises(self) -> None:
        """Test that unknown export format raises error."""
        with self.assertRaises(ValueError):
            self.model.export_events(format_type="xml")

    def test_clear_events(self) -> None:
        """Test clearing events."""
        # Add events
        event_capture.add_event("counter", "test", 1.0)
        time.sleep(0.1)
        self.assertGreater(self.model.event_count, 0)

        # Clear
        self.model.clear_events()
        self.assertEqual(self.model.event_count, 0)
        self.assertEqual(event_capture.get_event_count(), 0)

    def test_status_summary(self) -> None:
        """Test getting status summary."""
        self.model.enabled = True
        self.model.host = "0.0.0.0"
        self.model.port = 8888

        summary = self.model.get_status_summary()

        self.assertTrue(summary["enabled"])
        self.assertEqual(summary["host"], "0.0.0.0")
        self.assertEqual(summary["port"], 8888)
        self.assertIn("metrics_url", summary)
        self.assertIn("event_count", summary)

    def test_model_with_plugin(self) -> None:
        """Test model connection to plugin."""
        # Create mock plugin
        mock_plugin = HasTraits()
        mock_plugin.add_trait("enabled", Bool(True))
        mock_plugin.add_trait("host", Str("mock_host"))
        mock_plugin.add_trait("port", Int(9999))
        mock_plugin.add_trait("namespace", Str("mock_ns"))

        # Create model with plugin
        model = PrometheusObservabilityModel(plugin=mock_plugin)

        # Initial sync should happen
        time.sleep(0.1)

        # Note: We can't easily test trait observation in unit tests
        # but we verify the connection was attempted
        self.assertIsNotNone(model._plugin_ref)
        model.destroy()

    def test_event_max_1000(self) -> None:
        """Test that model limits events to 1000."""
        # Add many events
        for i in range(1500):
            event_capture.add_event("counter", f"test_{i}", float(i))

        time.sleep(0.2)

        # Should only keep last 1000
        self.assertLessEqual(self.model.event_count, 1000)


class TestModelEventHandling(unittest.TestCase):
    """Tests for model event handling from capture system."""

    def setUp(self) -> None:
        """Set up test."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def tearDown(self) -> None:
        """Clean up."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def test_model_receives_events(self) -> None:
        """Test that model receives events."""
        model = PrometheusObservabilityModel()

        # Add events
        event_capture.add_event("counter", "test_1", 1.0)
        event_capture.add_event("gauge", "test_2", 2.0)
        time.sleep(0.2)

        self.assertEqual(model.event_count, 2)
        model.destroy()

    def test_model_events_with_labels(self) -> None:
        """Test model capturing events with labels."""
        model = PrometheusObservabilityModel()

        event_capture.add_event(
            "counter",
            "test",
            1.0,
            labels={"device": "furnace", "phase": "heating"},
        )
        time.sleep(0.1)

        self.assertEqual(model.event_count, 1)
        event = model.events[0]
        self.assertEqual(event.labels["device"], "furnace")
        self.assertEqual(event.labels["phase"], "heating")

        model.destroy()

    def test_model_cleanup_on_destroy(self) -> None:
        """Test that model cleanup removes callbacks."""
        model = PrometheusObservabilityModel()

        # Callback should be registered
        self.assertTrue(model._event_callback_registered)
        initial_count = len(event_capture._event_callbacks)

        model.destroy()

        # Callback should be removed
        self.assertFalse(model._event_callback_registered)
        self.assertEqual(
            len(event_capture._event_callbacks),
            initial_count - 1,
        )


if __name__ == "__main__":
    unittest.main()
