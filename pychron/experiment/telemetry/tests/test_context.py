"""Tests for TelemetryContext correlation IDs."""

import unittest
from pychron.experiment.telemetry.context import TelemetryContext


class TestTelemetryContext(unittest.TestCase):
    """Test TelemetryContext for thread-safe correlation ID storage."""

    def setUp(self):
        """Clear context before each test."""
        TelemetryContext.clear()

    def tearDown(self):
        """Clear context after each test."""
        TelemetryContext.clear()

    def test_set_get_queue_id(self):
        """Test setting and getting queue ID."""
        queue_id = "test_queue"
        TelemetryContext.set_queue_id(queue_id)
        self.assertEqual(TelemetryContext.get_queue_id(), queue_id)

    def test_set_get_trace_id(self):
        """Test setting and getting trace ID."""
        trace_id = "trace_123"
        TelemetryContext.set_trace_id(trace_id)
        self.assertEqual(TelemetryContext.get_trace_id(), trace_id)

    def test_set_get_run_id(self):
        """Test setting and getting run ID."""
        run_id = "sample-001-00-00"
        TelemetryContext.set_run_id(run_id)
        self.assertEqual(TelemetryContext.get_run_id(), run_id)

    def test_set_get_run_uuid(self):
        """Test setting and getting run UUID."""
        run_uuid = "550e8400-e29b-41d4-a716-446655440000"
        TelemetryContext.set_run_uuid(run_uuid)
        self.assertEqual(TelemetryContext.get_run_uuid(), run_uuid)

    def test_push_pop_span_id(self):
        """Test span ID stack operations."""
        span1 = "span_1"
        span2 = "span_2"

        TelemetryContext.push_span_id(span1)
        TelemetryContext.push_span_id(span2)

        self.assertEqual(TelemetryContext.get_current_span_id(), span2)
        self.assertEqual(TelemetryContext.get_parent_span_id(), span1)

        popped = TelemetryContext.pop_span_id()
        self.assertEqual(popped, span2)
        self.assertEqual(TelemetryContext.get_current_span_id(), span1)

    def test_span_stack_empty(self):
        """Test span stack when empty."""
        self.assertIsNone(TelemetryContext.get_current_span_id())
        self.assertIsNone(TelemetryContext.get_parent_span_id())
        self.assertIsNone(TelemetryContext.pop_span_id())

    def test_span_stack_single_item(self):
        """Test parent span ID when only one span."""
        span = "span_1"
        TelemetryContext.push_span_id(span)

        self.assertEqual(TelemetryContext.get_current_span_id(), span)
        self.assertIsNone(TelemetryContext.get_parent_span_id())

    def test_clear_context(self):
        """Test clearing all context."""
        TelemetryContext.set_queue_id("queue")
        TelemetryContext.set_trace_id("trace")
        TelemetryContext.set_run_id("run")
        TelemetryContext.push_span_id("span")

        TelemetryContext.clear()

        self.assertIsNone(TelemetryContext.get_queue_id())
        self.assertIsNone(TelemetryContext.get_trace_id())
        self.assertIsNone(TelemetryContext.get_run_id())
        self.assertIsNone(TelemetryContext.get_current_span_id())


if __name__ == "__main__":
    unittest.main()
