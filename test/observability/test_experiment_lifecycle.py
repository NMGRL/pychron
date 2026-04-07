"""Tests for experiment lifecycle metrics."""

import time
import unittest
from pychron.observability import event_capture, metrics
from pychron.observability.config import MetricsConfig
from pychron.observability.experiment_lifecycle import (
    record_queue_started,
    record_queue_completed,
    record_run_started,
    record_run_completed,
    record_extraction_started,
    record_extraction_completed,
    record_measurement_started,
    record_measurement_completed,
    record_analysis_complete,
    record_age_calculated,
    record_phase_duration,
    record_run_duration,
)


class TestExperimentLifecycleMetrics(unittest.TestCase):
    """Test experiment lifecycle metric recording."""

    def setUp(self):
        """Setup test environment."""
        event_capture.clear_events()
        # Ensure metrics are enabled for tests
        config = MetricsConfig(enabled=True, namespace="pychron")
        metrics.configure(config)

    def tearDown(self):
        """Cleanup after tests."""
        event_capture.clear_events()

    def test_record_queue_started(self):
        """Test recording queue started event."""
        record_queue_started("test_queue", num_runs=5)
        time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.metric_name, "queue_started")
        self.assertEqual(event.event_type, "counter")
        self.assertEqual(event.value, 1.0)
        self.assertEqual(event.labels["queue"], "test_queue")
        self.assertEqual(event.labels["runs"], "5")

    def test_record_queue_completed(self):
        """Test recording queue completed event."""
        record_queue_completed("test_queue", status="success")
        time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.metric_name, "queue_completed")
        self.assertEqual(event.labels["status"], "success")

    def test_record_queue_failed(self):
        """Test recording failed queue."""
        record_queue_completed("test_queue", status="failed")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.labels["status"], "failed")

    def test_record_run_started(self):
        """Test recording run started event."""
        record_run_started("q1", "run_001", sample="S1", material="biotite")
        time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.metric_name, "run_started")
        self.assertEqual(event.labels["queue"], "q1")
        self.assertEqual(event.labels["run_id"], "run_001")
        self.assertEqual(event.labels["sample"], "S1")
        self.assertEqual(event.labels["material"], "biotite")

    def test_record_run_completed_success(self):
        """Test recording successful run completion."""
        record_run_completed("q1", "run_001", status="success")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "run_completed")
        self.assertEqual(event.labels["status"], "success")

    def test_record_run_completed_invalid(self):
        """Test recording invalid run."""
        record_run_completed("q1", "run_001", status="invalid")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.labels["status"], "invalid")

    def test_record_extraction_started(self):
        """Test recording extraction started."""
        record_extraction_started("q1", "run_001", extraction_type="laser")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "extraction_started")
        self.assertEqual(event.labels["type"], "laser")

    def test_record_extraction_completed(self):
        """Test recording extraction completed."""
        record_extraction_completed("q1", "run_001", status="success")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "extraction_completed")
        self.assertEqual(event.labels["status"], "success")

    def test_record_measurement_started(self):
        """Test recording measurement started."""
        record_measurement_started("q1", "run_001")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "measurement_started")

    def test_record_measurement_completed(self):
        """Test recording measurement completed."""
        record_measurement_completed("q1", "run_001", status="success")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "measurement_completed")

    def test_record_analysis_complete(self):
        """Test recording analysis complete."""
        record_analysis_complete("q1", "run_001", n_peaks=5)
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "analysis_complete")
        self.assertEqual(event.labels["n_peaks"], "5")

    def test_record_age_calculated(self):
        """Test recording age calculated."""
        record_age_calculated("q1", "run_001", age=42.5, material="biotite")
        time.sleep(0.1)

        events = event_capture.get_events()
        event = events[0]
        self.assertEqual(event.metric_name, "age_calculated")
        self.assertEqual(event.event_type, "gauge")
        self.assertEqual(event.value, 42.5)
        self.assertEqual(event.labels["material"], "biotite")

    def test_record_phase_duration_context_manager(self):
        """Test recording phase duration with context manager."""
        with record_phase_duration("extraction", "q1", "run_001"):
            time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.metric_name, "extraction_duration_seconds")
        self.assertEqual(event.event_type, "histogram")
        self.assertGreaterEqual(event.value, 0.08)  # Account for timing variance

    def test_record_run_duration_context_manager(self):
        """Test recording run duration with context manager."""
        with record_run_duration("q1", "run_001"):
            time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.metric_name, "run_duration_seconds")
        self.assertEqual(event.event_type, "histogram")
        self.assertGreaterEqual(event.value, 0.08)

    def test_complete_run_lifecycle(self):
        """Test complete run lifecycle with all major phases."""
        queue = "q1"
        run_id = "run_001"

        # Start queue
        record_queue_started(queue, num_runs=1)
        time.sleep(0.05)

        # Start run
        record_run_started(queue, run_id, sample="S1", material="biotite")
        time.sleep(0.05)

        # Extraction phase
        record_extraction_started(queue, run_id, extraction_type="laser")
        time.sleep(0.05)
        record_extraction_completed(queue, run_id, status="success")
        time.sleep(0.05)

        # Measurement phase
        record_measurement_started(queue, run_id)
        time.sleep(0.05)
        record_measurement_completed(queue, run_id, status="success")
        time.sleep(0.05)

        # Analysis
        record_analysis_complete(queue, run_id, n_peaks=3)
        time.sleep(0.05)

        # Age calculation
        record_age_calculated(queue, run_id, age=45.2, material="biotite")
        time.sleep(0.05)

        # Complete run
        record_run_completed(queue, run_id, status="success")
        time.sleep(0.05)

        # Complete queue
        record_queue_completed(queue, status="success")
        time.sleep(0.1)

        events = event_capture.get_events()
        self.assertEqual(len(events), 10)

        # Verify first event is queue_started
        self.assertEqual(events[0].metric_name, "queue_started")

        # Verify second event is run_started
        self.assertEqual(events[1].metric_name, "run_started")

        # Verify last event is queue_completed
        self.assertEqual(events[-1].metric_name, "queue_completed")

    def test_multiple_runs_in_queue(self):
        """Test multiple runs in a single queue."""
        queue = "q1"

        record_queue_started(queue, num_runs=3)
        time.sleep(0.05)

        # Run 1
        record_run_started(queue, "run_001")
        time.sleep(0.02)
        record_extraction_started(queue, "run_001")
        time.sleep(0.02)
        record_extraction_completed(queue, "run_001")
        time.sleep(0.02)
        record_run_completed(queue, "run_001", status="success")
        time.sleep(0.05)

        # Run 2
        record_run_started(queue, "run_002")
        time.sleep(0.02)
        record_extraction_started(queue, "run_002")
        time.sleep(0.02)
        record_extraction_completed(queue, "run_002")
        time.sleep(0.02)
        record_run_completed(queue, "run_002", status="success")
        time.sleep(0.05)

        # Run 3
        record_run_started(queue, "run_003")
        time.sleep(0.02)
        record_extraction_started(queue, "run_003")
        time.sleep(0.02)
        record_extraction_completed(queue, "run_003", status="failed")
        time.sleep(0.02)
        record_run_completed(queue, "run_003", status="failed")
        time.sleep(0.05)

        record_queue_completed(queue, status="completed_with_failures")
        time.sleep(0.1)

        events = event_capture.get_events()
        # 1 queue_started + 3*(run_started + extraction_started + extraction_completed
        # + run_completed) + 1 queue_completed = 1 + 12 + 1 = 14
        self.assertEqual(len(events), 14)

        # Count run_started events
        run_started = [e for e in events if e.metric_name == "run_started"]
        self.assertEqual(len(run_started), 3)

        # Count extraction events
        extraction = [e for e in events if "extraction" in e.metric_name]
        self.assertEqual(len(extraction), 6)  # 3 started + 3 completed


if __name__ == "__main__":
    unittest.main()
