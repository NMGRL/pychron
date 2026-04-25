"""Tests for experiment executor and watchdog metrics instrumentation."""

import unittest
from unittest.mock import MagicMock, patch

from pychron.observability.config import MetricsConfig
from pychron.observability.metrics import configure
from pychron.experiment import instrumentation


class TestExecutorMetricsQueue(unittest.TestCase):
    """Test queue lifecycle metrics."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))
        instrumentation._set_active_queue_count(0)
        instrumentation._set_active_run_count(0)

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    def test_record_queue_started(self, mock_gauge, mock_counter):
        """Test queue started metrics."""
        instrumentation._record_queue_started("queue1")

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("queue_starts_total", call_args[0])

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    def test_record_queue_completed(self, mock_gauge, mock_counter):
        """Test queue completed metrics."""
        instrumentation._record_queue_completed("queue1")

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("queue_completions_total", call_args[0])


class TestExecutorMetricsRuns(unittest.TestCase):
    """Test run lifecycle metrics."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))
        instrumentation._set_active_run_count(0)

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    def test_record_run_started(self, mock_gauge, mock_counter):
        """Test run started metrics."""
        instrumentation._record_run_started("run1")

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("runs_started_total", call_args[0])

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    @patch("pychron.observability.observe_histogram")
    def test_record_run_completed(self, mock_hist, mock_gauge, mock_counter):
        """Test run completed metrics."""
        instrumentation._record_run_completed("run1", 10.5)

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("runs_completed_total", call_args[0])

        # Histogram should be observed
        mock_hist.assert_called_once()
        hist_args = mock_hist.call_args
        self.assertIn("run_duration_seconds", hist_args[0])

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    @patch("pychron.observability.observe_histogram")
    def test_record_run_failed(self, mock_hist, mock_gauge, mock_counter):
        """Test run failed metrics."""
        instrumentation._record_run_failed("run1", 5.5)

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("runs_failed_total", call_args[0])

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.set_gauge")
    @patch("pychron.observability.observe_histogram")
    def test_record_run_canceled(self, mock_hist, mock_gauge, mock_counter):
        """Test run canceled metrics."""
        instrumentation._record_run_canceled("run1", 3.5)

        # Counter should be incremented
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("runs_canceled_total", call_args[0])


class TestExecutorMetricsPhases(unittest.TestCase):
    """Test phase metrics."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))

    @patch("pychron.observability.observe_histogram")
    def test_record_phase_duration_extraction(self, mock_hist):
        """Test phase duration metrics for extraction."""
        instrumentation._record_phase_duration("extraction", 2.5)

        mock_hist.assert_called_once()
        call_args = mock_hist.call_args
        self.assertIn("phase_duration_seconds", call_args[0])
        # Check that phase label is normalized
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("phase"), "extraction")

    @patch("pychron.observability.observe_histogram")
    def test_record_phase_duration_measurement(self, mock_hist):
        """Test phase duration metrics for measurement."""
        instrumentation._record_phase_duration("measurement", 5.0)

        mock_hist.assert_called_once()
        labelvalues = mock_hist.call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("phase"), "measurement")


class TestWatchdogMetrics(unittest.TestCase):
    """Test watchdog health check metrics."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))

    @patch("pychron.observability.inc_counter")
    def test_device_health_failure_recorded(self, mock_counter):
        """Test that device health check failures are recorded."""
        executor = MagicMock()
        from pychron.experiment.executor_watchdog_integration import ExecutorWatchdogIntegration

        watchdog = ExecutorWatchdogIntegration(executor)
        watchdog._record_device_health_metrics("extraction", False)

        # Counter should be called on failure
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("phase_healthcheck_failures_total", call_args[0])
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("phase"), "extraction")
        self.assertEqual(labelvalues.get("kind"), "device")

    @patch("pychron.observability.inc_counter")
    def test_device_health_success_not_recorded(self, mock_counter):
        """Test that successful device health checks are not recorded as failures."""
        executor = MagicMock()
        from pychron.experiment.executor_watchdog_integration import ExecutorWatchdogIntegration

        watchdog = ExecutorWatchdogIntegration(executor)
        watchdog._record_device_health_metrics("extraction", True)

        # Counter should not be called on success
        mock_counter.assert_not_called()

    @patch("pychron.observability.inc_counter")
    def test_service_health_failure_recorded(self, mock_counter):
        """Test that service health check failures are recorded."""
        executor = MagicMock()
        from pychron.experiment.executor_watchdog_integration import ExecutorWatchdogIntegration

        watchdog = ExecutorWatchdogIntegration(executor)
        watchdog._record_service_health_metrics("measurement", False)

        # Counter should be called on failure
        mock_counter.assert_called_once()
        call_args = mock_counter.call_args
        self.assertIn("phase_healthcheck_failures_total", call_args[0])
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("phase"), "measurement")
        self.assertEqual(labelvalues.get("kind"), "service")

    @patch("pychron.observability.inc_counter")
    def test_service_health_success_not_recorded(self, mock_counter):
        """Test that successful service health checks are not recorded as failures."""
        executor = MagicMock()
        from pychron.experiment.executor_watchdog_integration import ExecutorWatchdogIntegration

        watchdog = ExecutorWatchdogIntegration(executor)
        watchdog._record_service_health_metrics("measurement", True)

        # Counter should not be called on success
        mock_counter.assert_not_called()


class TestExecutorMetricsActiveCountTracking(unittest.TestCase):
    """Test active count tracking."""

    def test_set_and_get_active_queue_count(self):
        """Test setting and getting active queue count."""
        instrumentation._set_active_queue_count(3)
        self.assertEqual(instrumentation._get_active_queue_count(), 3)

    def test_active_queue_count_never_negative(self):
        """Test that active queue count never goes below zero."""
        instrumentation._set_active_queue_count(-1)
        self.assertEqual(instrumentation._get_active_queue_count(), 0)

    def test_set_and_get_active_run_count(self):
        """Test setting and getting active run count."""
        instrumentation._set_active_run_count(5)
        self.assertEqual(instrumentation._get_active_run_count(), 5)

    def test_active_run_count_never_negative(self):
        """Test that active run count never goes below zero."""
        instrumentation._set_active_run_count(-1)
        self.assertEqual(instrumentation._get_active_run_count(), 0)


if __name__ == "__main__":
    unittest.main()
