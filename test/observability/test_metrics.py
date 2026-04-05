"""Tests for metrics facade and registry."""

import unittest
from unittest.mock import MagicMock, patch

from pychron.observability.config import MetricsConfig
from pychron.observability.metrics import (
    configure,
    get_config,
    inc_counter,
    is_enabled,
    observe_duration,
    observe_histogram,
    set_gauge,
)


class TestMetricsDisabled(unittest.TestCase):
    """Test metrics behavior when disabled."""

    def setUp(self) -> None:
        """Set up test with metrics disabled."""
        configure(MetricsConfig(enabled=False))

    def test_is_disabled(self) -> None:
        """Test that metrics are disabled."""
        self.assertFalse(is_enabled())

    def test_counter_noop_when_disabled(self) -> None:
        """Test that counter is no-op when disabled."""
        # Should not raise or crash
        inc_counter(
            "test_counter",
            "Test counter",
            labels=["test"],
            labelvalues={"test": "value"},
        )

    def test_gauge_noop_when_disabled(self) -> None:
        """Test that gauge is no-op when disabled."""
        # Should not raise or crash
        set_gauge(
            "test_gauge",
            "Test gauge",
            42.0,
            labels=["test"],
            labelvalues={"test": "value"},
        )

    def test_histogram_noop_when_disabled(self) -> None:
        """Test that histogram is no-op when disabled."""
        # Should not raise or crash
        observe_histogram(
            "test_histogram",
            "Test histogram",
            1.5,
            labels=["test"],
            labelvalues={"test": "value"},
        )

    def test_duration_context_manager_noop_when_disabled(self) -> None:
        """Test that duration context manager is no-op when disabled."""
        with observe_duration(
            "test_duration",
            "Test duration",
            labels=["test"],
            labelvalues={"test": "value"},
        ):
            pass  # Should not crash


class TestMetricsEnabled(unittest.TestCase):
    """Test metrics behavior when enabled."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="test"))

    def test_is_enabled(self) -> None:
        """Test that metrics are enabled."""
        self.assertTrue(is_enabled())

    def test_counter_increment(self) -> None:
        """Test counter increment."""
        inc_counter(
            "test_counter",
            "Test counter",
            labels=["result"],
            labelvalues={"result": "success"},
        )
        # If no exception, test passes

    def test_counter_without_labels(self) -> None:
        """Test counter without labels."""
        inc_counter("test_counter_nolabel", "Test counter without labels")
        # If no exception, test passes

    def test_gauge_set(self) -> None:
        """Test gauge set."""
        set_gauge(
            "test_gauge",
            "Test gauge",
            42.0,
            labels=["phase"],
            labelvalues={"phase": "extraction"},
        )
        # If no exception, test passes

    def test_gauge_without_labels(self) -> None:
        """Test gauge without labels."""
        set_gauge("test_gauge_nolabel", "Test gauge without labels", 10.5)
        # If no exception, test passes

    def test_histogram_observe(self) -> None:
        """Test histogram observe."""
        observe_histogram(
            "test_histogram",
            "Test histogram",
            1.5,
            labels=["device"],
            labelvalues={"device": "laser"},
        )
        # If no exception, test passes

    def test_histogram_without_labels(self) -> None:
        """Test histogram without labels."""
        observe_histogram(
            "test_histogram_nolabel",
            "Test histogram without labels",
            2.5,
        )
        # If no exception, test passes

    def test_histogram_with_custom_buckets(self) -> None:
        """Test histogram with custom buckets."""
        custom_buckets = (0.1, 0.5, 1.0, 2.0, 5.0)
        observe_histogram(
            "test_histogram_buckets",
            "Test histogram with buckets",
            0.75,
            buckets=custom_buckets,
        )
        # If no exception, test passes

    def test_duration_context_manager(self) -> None:
        """Test duration context manager."""
        with observe_duration(
            "test_duration",
            "Test duration",
            labels=["operation"],
            labelvalues={"operation": "io"},
        ):
            pass
        # If no exception, test passes

    def test_repeated_metric_access(self) -> None:
        """Test repeated metric access does not crash."""
        # Access the same metric multiple times
        for _ in range(3):
            inc_counter("repeated_counter", "Repeated counter")
            set_gauge("repeated_gauge", "Repeated gauge", 5.0)
            observe_histogram("repeated_histogram", "Repeated histogram", 0.5)


class TestConfigManagement(unittest.TestCase):
    """Test configuration management."""

    def test_get_config_returns_default_when_not_configured(self) -> None:
        """Test get_config returns default when not configured."""
        from pychron.observability import metrics as metrics_module

        # Reset to unconfigured state
        metrics_module._config = None
        config = get_config()
        self.assertFalse(config.enabled)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 9109)
        self.assertEqual(config.namespace, "pychron")

    def test_configure_sets_config(self) -> None:
        """Test that configure sets the configuration."""
        config = MetricsConfig(
            enabled=True,
            host="0.0.0.0",
            port=8888,
            namespace="custom",
        )
        configure(config)
        retrieved = get_config()
        self.assertTrue(retrieved.enabled)
        self.assertEqual(retrieved.host, "0.0.0.0")
        self.assertEqual(retrieved.port, 8888)
        self.assertEqual(retrieved.namespace, "custom")

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        config = MetricsConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 9109)
        self.assertEqual(config.namespace, "pychron")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in metrics operations."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, namespace="test"))

    def test_invalid_labelvalues_are_handled(self) -> None:
        """Test that invalid label values are handled gracefully."""
        # Try to use labels not defined in the metric
        # This should not crash
        inc_counter("test_counter", "Test counter", labels=["a"])
        # Next call with different labels should still work
        inc_counter("test_counter", "Test counter", labels=["a"], labelvalues={"a": "1"})


if __name__ == "__main__":
    unittest.main()
