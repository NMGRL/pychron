"""Tests for device I/O metrics instrumentation."""

import unittest
from unittest.mock import MagicMock, patch

from pychron.observability.config import MetricsConfig
from pychron.observability.metrics import configure
from pychron.experiment.telemetry.device_io import (
    telemetry_device_io,
    TelemetryDeviceIOContext,
    telemetry_device_io_context,
)


class TestDeviceIOMetrics(unittest.TestCase):
    """Test device I/O metrics recording."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Reset global state if needed
        pass

    @patch("pychron.experiment.telemetry.device_io._record_prometheus_device_io_metrics")
    def test_decorator_records_metrics_on_success(self, mock_metrics: MagicMock) -> None:
        """Test that decorator records metrics on success."""
        recorder = MagicMock()

        @telemetry_device_io("laser", "fire", recorder)
        def fire_laser():
            return True

        result = fire_laser()

        self.assertTrue(result)
        # Metrics should be called
        mock_metrics.assert_called_once()
        args, kwargs = mock_metrics.call_args
        self.assertEqual(args[0], "laser")
        self.assertEqual(args[1], "fire")
        self.assertTrue(args[3])  # success=True

    @patch("pychron.experiment.telemetry.device_io._record_prometheus_device_io_metrics")
    def test_decorator_records_metrics_on_failure(self, mock_metrics: MagicMock) -> None:
        """Test that decorator records metrics on failure."""
        recorder = MagicMock()

        @telemetry_device_io("valve", "open", recorder)
        def open_valve():
            raise ValueError("Valve stuck")

        with self.assertRaises(ValueError):
            open_valve()

        # Metrics should be called even on failure
        mock_metrics.assert_called_once()
        args, kwargs = mock_metrics.call_args
        self.assertEqual(args[0], "valve")
        self.assertEqual(args[1], "open")
        self.assertFalse(args[3])  # success=False

    @patch("pychron.experiment.telemetry.device_io._record_prometheus_device_io_metrics")
    def test_context_manager_records_metrics_on_success(self, mock_metrics: MagicMock) -> None:
        """Test that context manager records metrics on success."""
        recorder = MagicMock()

        with telemetry_device_io_context("spectrometer", "read", recorder):
            pass

        # Metrics should be called
        mock_metrics.assert_called_once()
        args, kwargs = mock_metrics.call_args
        self.assertEqual(args[0], "spectrometer")
        self.assertEqual(args[1], "read")
        self.assertTrue(args[3])  # success=True

    @patch("pychron.experiment.telemetry.device_io._record_prometheus_device_io_metrics")
    def test_context_manager_records_metrics_on_failure(self, mock_metrics: MagicMock) -> None:
        """Test that context manager records metrics on failure."""
        recorder = MagicMock()

        with self.assertRaises(RuntimeError):
            with telemetry_device_io_context("pump", "start", recorder):
                raise RuntimeError("Pump failed")

        # Metrics should be called even on failure
        mock_metrics.assert_called_once()
        args, kwargs = mock_metrics.call_args
        self.assertEqual(args[0], "pump")
        self.assertEqual(args[1], "start")
        self.assertFalse(args[3])  # success=False

    @patch("pychron.experiment.telemetry.device_io._record_prometheus_device_io_metrics")
    def test_metrics_duration_is_seconds(self, mock_metrics: MagicMock) -> None:
        """Test that metrics duration is recorded in seconds."""
        recorder = MagicMock()

        with telemetry_device_io_context("device", "operation", recorder):
            pass

        # Check that duration is in seconds (should be a small positive number)
        duration = mock_metrics.call_args[0][2]
        self.assertGreater(duration, 0)
        self.assertLess(duration, 1)  # Should be very fast

    def test_decorator_without_recorder_is_noop(self) -> None:
        """Test that decorator works without recorder."""

        @telemetry_device_io("laser", "fire", None)
        def fire_laser():
            return 42

        result = fire_laser()
        self.assertEqual(result, 42)

    def test_context_manager_without_recorder_is_noop(self) -> None:
        """Test that context manager works without recorder."""
        with telemetry_device_io_context("laser", "fire", None):
            pass


class TestDeviceIOMetricsLabelNormalization(unittest.TestCase):
    """Test metrics label normalization."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="pychron"))

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.observe_histogram")
    @patch("pychron.observability.set_gauge")
    def test_device_name_normalization(self, mock_gauge, mock_histogram, mock_counter):
        """Test that device names are normalized."""
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        _record_prometheus_device_io_metrics(
            "Laser Device",
            "fire_laser",
            0.1,
            True,
        )

        # Check that normalized names are used in labels
        # Device name should be lowercase and spaces replaced with underscores
        call_args = mock_counter.call_args
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("device"), "laser_device")

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.observe_histogram")
    @patch("pychron.observability.set_gauge")
    def test_operation_name_normalization(self, mock_gauge, mock_histogram, mock_counter):
        """Test that operation names are normalized."""
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        _record_prometheus_device_io_metrics(
            "laser",
            "Fire Laser Operation",
            0.1,
            True,
        )

        # Check that normalized names are used in labels
        call_args = mock_counter.call_args
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("operation"), "fire_laser_operation")

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.observe_histogram")
    @patch("pychron.observability.set_gauge")
    def test_result_label_on_success(self, mock_gauge, mock_histogram, mock_counter):
        """Test that result label is set to success on success."""
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        _record_prometheus_device_io_metrics("laser", "fire", 0.1, True)

        call_args = mock_counter.call_args
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("result"), "success")

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.observe_histogram")
    @patch("pychron.observability.set_gauge")
    def test_result_label_on_failure(self, mock_gauge, mock_histogram, mock_counter):
        """Test that result label is set to failure on failure."""
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        _record_prometheus_device_io_metrics("laser", "fire", 0.1, False)

        call_args = mock_counter.call_args
        labelvalues = call_args.kwargs.get("labelvalues", {})
        self.assertEqual(labelvalues.get("result"), "failure")

    @patch("pychron.observability.inc_counter")
    @patch("pychron.observability.observe_histogram")
    @patch("pychron.observability.set_gauge")
    def test_last_success_only_on_success(self, mock_gauge, mock_histogram, mock_counter):
        """Test that last success timestamp is only recorded on success."""
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        # Record failure
        _record_prometheus_device_io_metrics("laser", "fire", 0.1, False)
        mock_gauge.reset_mock()

        # Record success
        _record_prometheus_device_io_metrics("laser", "fire", 0.1, True)

        # Gauge should only be called for success
        mock_gauge.assert_called_once()
        call_args = mock_gauge.call_args
        self.assertIn("device_last_success_timestamp_seconds", call_args[0])


if __name__ == "__main__":
    unittest.main()
