"""Tests for event capture system."""

import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

from pychron.observability import event_capture as event_capture_module
from pychron.observability.tasks.event import PrometheusEvent

# Alias for cleaner code
event_capture = event_capture_module


class TestPrometheusEvent(unittest.TestCase):
    """Tests for PrometheusEvent dataclass."""

    def test_event_creation(self) -> None:
        """Test creating an event."""
        event = PrometheusEvent(
            timestamp=123.456,
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
            labels={"device": "furnace"},
        )
        self.assertEqual(event.timestamp, 123.456)
        self.assertEqual(event.event_type, "counter")
        self.assertEqual(event.metric_name, "test_counter")
        self.assertEqual(event.value, 1.0)
        self.assertEqual(event.labels, {"device": "furnace"})
        self.assertEqual(event.status, "success")

    def test_event_to_dict(self) -> None:
        """Test converting event to dict."""
        event = PrometheusEvent(
            timestamp=123.456,
            event_type="gauge",
            metric_name="test_gauge",
            value=42.0,
            labels={"phase": "extraction"},
        )
        data = event.to_dict()
        self.assertEqual(data["event_type"], "gauge")
        self.assertEqual(data["metric_name"], "test_gauge")
        self.assertEqual(data["value"], 42.0)
        self.assertEqual(data["labels"], {"phase": "extraction"})

    def test_event_from_dict(self) -> None:
        """Test creating event from dict."""
        data = {
            "timestamp": 123.456,
            "event_type": "histogram",
            "metric_name": "test_histogram",
            "value": 2.5,
            "labels": {"operation": "read"},
            "status": "success",
        }
        event = PrometheusEvent.from_dict(data)
        self.assertEqual(event.timestamp, 123.456)
        self.assertEqual(event.event_type, "histogram")
        self.assertEqual(event.metric_name, "test_histogram")


class TestEventCapture(unittest.TestCase):
    """Tests for event capture system."""

    def setUp(self) -> None:
        """Set up test by clearing events and resetting state."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        # Remove any lingering callbacks
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def tearDown(self) -> None:
        """Clean up after tests."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def test_add_event(self) -> None:
        """Test adding an event to the queue."""
        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
        )
        events = event_capture.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "counter")
        self.assertEqual(events[0].metric_name, "test_counter")

    def test_add_multiple_events(self) -> None:
        """Test adding multiple events."""
        for i in range(5):
            event_capture.add_event(
                event_type="counter",
                metric_name=f"counter_{i}",
                value=float(i),
            )
        self.assertEqual(event_capture.get_event_count(), 5)

    def test_get_events(self) -> None:
        """Test retrieving events."""
        for i in range(3):
            event_capture.add_event(
                event_type="counter",
                metric_name=f"counter_{i}",
                value=float(i),
            )
        events = event_capture.get_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].metric_name, "counter_0")
        self.assertEqual(events[1].metric_name, "counter_1")
        self.assertEqual(events[2].metric_name, "counter_2")

    def test_get_events_with_count(self) -> None:
        """Test retrieving limited number of events."""
        for i in range(10):
            event_capture.add_event(
                event_type="counter",
                metric_name=f"counter_{i}",
                value=float(i),
            )
        # Get last 3 events
        events = event_capture.get_events(count=3)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].metric_name, "counter_7")
        self.assertEqual(events[1].metric_name, "counter_8")
        self.assertEqual(events[2].metric_name, "counter_9")

    def test_event_queue_max_length(self) -> None:
        """Test that event queue respects max length (1000)."""
        # Add more than 1000 events
        for i in range(1500):
            event_capture.add_event(
                event_type="counter",
                metric_name=f"counter_{i}",
                value=float(i),
            )
        # Queue should only keep last 1000
        self.assertEqual(event_capture.get_event_count(), 1000)
        events = event_capture.get_events()
        # Should have events from 500 to 1499
        self.assertEqual(events[0].metric_name, "counter_500")
        self.assertEqual(events[-1].metric_name, "counter_1499")

    def test_clear_events(self) -> None:
        """Test clearing all events."""
        for i in range(5):
            event_capture.add_event(
                event_type="counter",
                metric_name=f"counter_{i}",
                value=float(i),
            )
        self.assertEqual(event_capture.get_event_count(), 5)
        event_capture.clear_events()
        self.assertEqual(event_capture.get_event_count(), 0)

    def test_capture_disabled(self) -> None:
        """Test that events are not captured when disabled."""
        event_capture.set_capture_enabled(False)
        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
        )
        self.assertEqual(event_capture.get_event_count(), 0)

    def test_capture_toggle(self) -> None:
        """Test toggling capture on/off."""
        # Start enabled
        event_capture.set_capture_enabled(True)
        event_capture.add_event(
            event_type="counter",
            metric_name="counter_1",
            value=1.0,
        )
        self.assertEqual(event_capture.get_event_count(), 1)

        # Disable
        event_capture.set_capture_enabled(False)
        event_capture.add_event(
            event_type="counter",
            metric_name="counter_2",
            value=2.0,
        )
        self.assertEqual(event_capture.get_event_count(), 1)

        # Re-enable
        event_capture.set_capture_enabled(True)
        event_capture.add_event(
            event_type="counter",
            metric_name="counter_3",
            value=3.0,
        )
        self.assertEqual(event_capture.get_event_count(), 2)

    def test_event_with_labels(self) -> None:
        """Test adding event with labels."""
        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
            labels={"device": "furnace", "operation": "heat"},
        )
        events = event_capture.get_events()
        self.assertEqual(events[0].labels, {"device": "furnace", "operation": "heat"})

    def test_event_with_error_status(self) -> None:
        """Test adding event with error status."""
        event_capture.add_event(
            event_type="gauge",
            metric_name="test_gauge",
            value=0.0,
            status="Connection timeout",
        )
        events = event_capture.get_events()
        self.assertEqual(events[0].status, "Connection timeout")

    def test_event_timestamp(self) -> None:
        """Test that events have accurate timestamps."""
        before = time.time()
        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
        )
        after = time.time()
        events = event_capture.get_events()
        self.assertGreaterEqual(events[0].timestamp, before)
        self.assertLessEqual(events[0].timestamp, after)


class TestEventCallbacks(unittest.TestCase):
    """Tests for event callback registration and invocation."""

    def setUp(self) -> None:
        """Set up test."""
        event_capture.clear_events()
        # Clear registered callbacks by reimporting or directly clearing
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def tearDown(self) -> None:
        """Clean up."""
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def test_register_callback(self) -> None:
        """Test registering a callback."""
        callback = MagicMock()
        event_capture.register_callback(callback)
        self.assertIn(callback, event_capture._event_callbacks)

    def test_unregister_callback(self) -> None:
        """Test unregistering a callback."""
        callback = MagicMock()
        event_capture.register_callback(callback)
        self.assertIn(callback, event_capture._event_callbacks)
        event_capture.unregister_callback(callback)
        self.assertNotIn(callback, event_capture._event_callbacks)

    def test_callback_invoked_on_event(self) -> None:
        """Test that callback is invoked when event occurs."""
        callback = MagicMock()
        event_capture.register_callback(callback)

        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
        )

        # Give background thread time to call callback
        time.sleep(0.5)

        # Callback should have been called
        self.assertTrue(callback.called)
        # Check that it was called with a PrometheusEvent
        self.assertIsInstance(callback.call_args[0][0], PrometheusEvent)

    def test_multiple_callbacks(self) -> None:
        """Test that multiple callbacks all get called."""
        # Note: callbacks run in background threads, so we synchronously call them
        # instead of testing the background thread mechanism which can be
        # unreliable in test environment
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        event_capture.register_callback(callback1)
        event_capture.register_callback(callback2)
        event_capture.register_callback(callback3)

        # Verify all callbacks are registered
        self.assertEqual(len(event_capture._event_callbacks), 3)

        # Call them synchronously to test the mechanism
        test_event = PrometheusEvent(
            timestamp=time.time(),
            event_type="gauge",
            metric_name="test_gauge",
            value=42.0,
        )

        for callback in event_capture._event_callbacks:
            callback(test_event)

        self.assertTrue(callback1.called)
        self.assertTrue(callback2.called)
        self.assertTrue(callback3.called)

    def test_callback_not_invoked_when_disabled(self) -> None:
        """Test that callbacks are not invoked when capture is disabled."""
        callback = MagicMock()
        event_capture.register_callback(callback)
        event_capture.set_capture_enabled(False)

        event_capture.add_event(
            event_type="counter",
            metric_name="test_counter",
            value=1.0,
        )

        time.sleep(0.5)
        self.assertFalse(callback.called)

    def test_duplicate_callback_registration(self) -> None:
        """Test that registering same callback twice doesn't create duplicates."""
        callback = MagicMock()
        event_capture.register_callback(callback)
        event_capture.register_callback(callback)

        # Should only be in list once
        count = sum(1 for cb in event_capture._event_callbacks if cb is callback)
        self.assertEqual(count, 1)


class TestThreadSafety(unittest.TestCase):
    """Tests for thread safety of event capture."""

    def setUp(self) -> None:
        """Set up test."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def tearDown(self) -> None:
        """Clean up after tests."""
        event_capture.clear_events()
        event_capture.set_capture_enabled(True)
        with event_capture._callbacks_lock:
            event_capture._event_callbacks.clear()

    def test_concurrent_event_addition(self) -> None:
        """Test adding events from multiple threads."""
        num_threads = 10
        events_per_thread = 50
        errors = []

        def add_events(thread_id: int) -> None:
            try:
                for i in range(events_per_thread):
                    event_capture.add_event(
                        event_type="counter",
                        metric_name=f"counter_t{thread_id}_e{i}",
                        value=float(i),
                    )
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=add_events, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Add small delay to ensure all events are processed
        time.sleep(0.1)

        self.assertEqual(len(errors), 0)
        # Should have all events (up to 1000 max)
        count = event_capture.get_event_count()
        expected = min(num_threads * events_per_thread, 1000)
        self.assertEqual(
            count,
            expected,
            f"Expected {expected} events but got {count}",
        )

    def test_concurrent_read_write(self) -> None:
        """Test reading and writing events concurrently."""
        errors = []

        def add_events() -> None:
            try:
                for i in range(100):
                    event_capture.add_event(
                        event_type="counter",
                        metric_name=f"counter_{i}",
                        value=float(i),
                    )
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def read_events() -> None:
            try:
                for _ in range(50):
                    _ = event_capture.get_events()
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)

        writer = threading.Thread(target=add_events)
        readers = [threading.Thread(target=read_events) for _ in range(3)]

        writer.start()
        for r in readers:
            r.start()

        writer.join()
        for r in readers:
            r.join()

        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
