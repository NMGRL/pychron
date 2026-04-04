"""Tests for TelemetryEvent schema."""

import json
import unittest
from pychron.experiment.telemetry.event import TelemetryEvent, TelemetryLevel, EventType


class TestTelemetryEvent(unittest.TestCase):
    """Test TelemetryEvent schema and serialization."""

    def test_create_basic_event(self):
        """Test creating a basic telemetry event."""
        event = TelemetryEvent(
            event_type="test_event", ts=1234567890.0, level="info", component="test"
        )
        self.assertEqual(event.event_type, "test_event")
        self.assertEqual(event.level, "info")
        self.assertEqual(event.component, "test")

    def test_create_with_factory_method(self):
        """Test creating event with factory method."""
        event = TelemetryEvent.create(
            event_type="test_event",
            component="test_component",
            action="test_action",
            queue_id="test_queue",
        )
        self.assertEqual(event.event_type, "test_event")
        self.assertEqual(event.component, "test_component")
        self.assertEqual(event.action, "test_action")
        self.assertEqual(event.queue_id, "test_queue")
        self.assertIsNotNone(event.ts)  # Should be set by factory

    def test_to_dict_serialization(self):
        """Test event serialization to dictionary."""
        event = TelemetryEvent(
            event_type="test",
            ts=1234567890.0,
            level="info",
            queue_id="queue1",
            run_id="run1",
            component="test",
        )
        d = event.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["event_type"], "test")
        self.assertEqual(d["queue_id"], "queue1")

    def test_to_dict_with_enum_values(self):
        """Test that enums are converted to strings in to_dict()."""
        event = TelemetryEvent(
            event_type=EventType.STATE_TRANSITION.value,
            ts=1234567890.0,
            level=TelemetryLevel.INFO.value,
            component="test",
        )
        d = event.to_dict()
        # Should be strings, not enums
        self.assertIsInstance(d["event_type"], str)
        self.assertIsInstance(d["level"], str)

    def test_json_serialization(self):
        """Test that event can be serialized to JSON."""
        event = TelemetryEvent.create(
            event_type="test", component="test", action="test_action", payload={"key": "value"}
        )
        json_str = json.dumps(event.to_dict(), default=str)
        self.assertIsInstance(json_str, str)

        # Should be able to parse it back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["event_type"], "test")
        self.assertEqual(parsed["component"], "test")

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        event = TelemetryEvent(event_type="test", ts=1234567890.0, level="info")
        # All optional fields should be None
        self.assertIsNone(event.queue_id)
        self.assertIsNone(event.run_id)
        self.assertIsNone(event.trace_id)
        self.assertIsNone(event.state_from)
        self.assertIsNone(event.duration_ms)
        self.assertIsNone(event.error)


if __name__ == "__main__":
    unittest.main()
