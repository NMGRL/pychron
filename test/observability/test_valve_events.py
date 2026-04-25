"""Test valve operations trigger Prometheus events."""

import unittest
from unittest.mock import Mock, MagicMock, patch

from pychron.observability import event_capture


class TestValvePrometheusEvents(unittest.TestCase):
    """Test that valve operations trigger observability events."""

    def setUp(self):
        """Set up test fixtures."""
        event_capture.clear_events()

    def tearDown(self):
        """Clean up after tests."""
        event_capture.clear_events()

    def _create_manager(self):
        """Create an ExtractionLineManager with mocked dependencies."""
        from pychron.extraction_line.extraction_line_manager import (
            ExtractionLineManager,
        )

        manager = ExtractionLineManager()
        manager.application = Mock()
        manager.application.get_service = Mock(return_value=None)
        return manager

    def test_valve_open_triggers_event(self):
        """Test that opening a valve triggers a Prometheus event."""
        manager = self._create_manager()

        initial_events = len(event_capture.get_events())

        manager._log_spec_event("VALVE-C", "open")

        # Verify event was captured
        new_events = event_capture.get_events()[initial_events:]
        self.assertEqual(len(new_events), 1)

        event = new_events[0]
        self.assertEqual(event.metric_name, "valve_open")
        self.assertEqual(event.event_type, "counter")
        self.assertEqual(event.value, 1.0)
        self.assertEqual(event.labels["valve"], "VALVE-C")
        self.assertEqual(event.status, "success")

    def test_valve_close_triggers_event(self):
        """Test that closing a valve triggers a Prometheus event."""
        manager = self._create_manager()

        initial_events = len(event_capture.get_events())

        manager._log_spec_event("VALVE-A", "close")

        new_events = event_capture.get_events()[initial_events:]
        self.assertEqual(len(new_events), 1)

        event = new_events[0]
        self.assertEqual(event.metric_name, "valve_close")
        self.assertEqual(event.event_type, "counter")
        self.assertEqual(event.value, 1.0)
        self.assertEqual(event.labels["valve"], "VALVE-A")
        self.assertEqual(event.status, "success")

    def test_multiple_valve_operations_trigger_events(self):
        """Test that multiple valve operations trigger multiple events."""
        manager = self._create_manager()

        initial_events = len(event_capture.get_events())

        # Simulate multiple valve operations
        manager._log_spec_event("VALVE-C", "open")
        manager._log_spec_event("VALVE-C", "close")
        manager._log_spec_event("VALVE-A", "open")

        new_events = event_capture.get_events()[initial_events:]
        self.assertEqual(len(new_events), 3)

        # Verify sequence
        self.assertEqual(new_events[0].metric_name, "valve_open")
        self.assertEqual(new_events[0].labels["valve"], "VALVE-C")

        self.assertEqual(new_events[1].metric_name, "valve_close")
        self.assertEqual(new_events[1].labels["valve"], "VALVE-C")

        self.assertEqual(new_events[2].metric_name, "valve_open")
        self.assertEqual(new_events[2].labels["valve"], "VALVE-A")


if __name__ == "__main__":
    unittest.main()
