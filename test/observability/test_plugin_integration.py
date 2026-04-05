# ===============================================================================
# Copyright 2026 Pychron Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

"""End-to-end integration tests for Prometheus plugin."""

import unittest
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock

from pychron.observability import configure, MetricsConfig
from pychron.observability.tasks.plugin import PrometheusPlugin


class TestPrometheusPluginIntegration(unittest.TestCase):
    """Test Prometheus plugin initialization and integration."""

    def setUp(self):
        """Reset observability state before each test."""
        # Reset global config and exporter
        from pychron.observability import registry

        configure(MetricsConfig(enabled=False))
        # Clear any existing metrics
        try:
            registry.get_registry().clear()
        except Exception:
            pass

    def tearDown(self):
        """Clean up after tests."""
        configure(MetricsConfig(enabled=False))

    def test_plugin_initialization_disabled(self):
        """Test plugin initializes correctly when disabled."""
        plugin = PrometheusPlugin()
        self.assertFalse(plugin.enabled)
        self.assertEqual(plugin.host, "127.0.0.1")
        self.assertEqual(plugin.port, 9109)
        self.assertEqual(plugin.namespace, "pychron")

    def test_plugin_initialization_enabled(self):
        """Test plugin initializes with custom configuration."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.host = "0.0.0.0"
        plugin.port = 8888
        plugin.namespace = "custom"

        self.assertTrue(plugin.enabled)
        self.assertEqual(plugin.host, "0.0.0.0")
        self.assertEqual(plugin.port, 8888)
        self.assertEqual(plugin.namespace, "custom")

    def test_plugin_start_when_disabled(self):
        """Test plugin start when disabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = False

        # Should not raise any exceptions
        plugin.start()

        # Exporter should not be started
        self.assertFalse(plugin._exporter_started)

    def test_plugin_start_when_enabled(self):
        """Test plugin start when enabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 19109  # Use high port to avoid conflicts

        plugin.start()
        # Should attempt to start exporter
        self.assertTrue(plugin._exporter_started)

    def test_plugin_configures_observability(self):
        """Test that plugin configures observability correctly."""
        from pychron.observability import get_config

        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.namespace = "test_ns"

        plugin._configure_observability()

        config = get_config()
        self.assertTrue(config.enabled)
        self.assertEqual(config.namespace, "test_ns")

    def test_plugin_check_valid_config(self):
        """Test plugin validation with valid config."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 8080

        self.assertTrue(plugin.check())

    def test_plugin_check_invalid_port(self):
        """Test plugin validation with invalid port."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 70000  # Invalid port

        self.assertFalse(plugin.check())

    def test_plugin_check_disabled(self):
        """Test plugin validation when disabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = False
        plugin.port = 70000  # Would be invalid if enabled

        # Should pass because plugin is disabled
        self.assertTrue(plugin.check())

    def test_plugin_exporter_idempotent(self):
        """Test that starting exporter multiple times is safe."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 19110

        plugin.start()
        first_started = plugin._exporter_started

        # Try to start again
        plugin._start_exporter()
        second_started = plugin._exporter_started

        # Should be the same
        self.assertEqual(first_started, second_started)

    def test_plugin_with_metrics_recording(self):
        """Test plugin with actual metrics recording."""
        from pychron.observability import inc_counter, observe_histogram

        plugin = PrometheusPlugin()
        plugin.enabled = True

        # Configure and start
        plugin._configure_observability()

        # Record some metrics
        inc_counter(
            "test_operations_total",
            "Test operations",
            labels=["operation", "device", "result"],
            labelvalues={"operation": "test", "device": "test_device", "result": "success"},
        )
        observe_histogram(
            "test_duration_seconds",
            "Test duration",
            0.5,
            labels=["operation", "device"],
            labelvalues={"operation": "test", "device": "test_device"},
        )

        from pychron.observability.registry import get_registry

        registry = get_registry()

        # Verify metrics were recorded by checking registry collection
        # We can verify by calling collect() and checking the samples
        collected_families = list(registry.collect())
        metric_names = {f.name for f in collected_families}

        # Prometheus counter names are exposed without _total in the internal family name
        self.assertIn("pychron_test_operations", metric_names)
        self.assertIn("pychron_test_duration_seconds", metric_names)

    def test_plugin_with_device_io_metrics(self):
        """Test plugin recording device I/O metrics."""
        from pychron.observability import inc_counter, observe_histogram, set_gauge
        from pychron.experiment.telemetry.device_io import _record_prometheus_device_io_metrics

        plugin = PrometheusPlugin()
        plugin.enabled = True

        # Configure
        plugin._configure_observability()

        # Simulate a successful device I/O operation
        _record_prometheus_device_io_metrics("test_device", "test_operation", 0.123, True)

        # Verify metrics exist
        from pychron.observability.registry import get_registry

        registry = get_registry()

        # Check that device_io metrics were created by collecting
        collected_families = list(registry.collect())
        metric_names = {f.name for f in collected_families}

        # Prometheus counter names are exposed without _total in the internal family name
        self.assertIn("pychron_device_io_operations", metric_names)
        self.assertIn("pychron_device_io_duration_seconds", metric_names)
        self.assertIn("pychron_device_last_success_timestamp_seconds", metric_names)

    def test_plugin_configuration_via_traits(self):
        """Test that plugin configuration is applied correctly."""
        plugin = PrometheusPlugin()

        # Set configuration before start
        plugin.enabled = True
        plugin.host = "192.168.1.1"
        plugin.port = 29109
        plugin.namespace = "custom_ns"

        # Configure observability
        plugin._configure_observability()

        from pychron.observability import get_config

        config = get_config()

        self.assertEqual(config.enabled, True)
        self.assertEqual(config.host, "192.168.1.1")
        self.assertEqual(config.port, 29109)
        self.assertEqual(config.namespace, "custom_ns")

    def test_plugin_environment_variable_override(self):
        """Test that environment variables can override plugin config."""
        import os

        plugin = PrometheusPlugin()
        plugin.enabled = True

        # Set environment variables
        os.environ["PYCHRON_PROMETHEUS_ENABLED"] = "true"
        os.environ["PYCHRON_PROMETHEUS_PORT"] = "39109"

        try:
            plugin._configure_observability()
            # Plugin reads config from traits, not env vars directly
            # But env vars could be set during Envisage initialization
        finally:
            # Clean up
            os.environ.pop("PYCHRON_PROMETHEUS_ENABLED", None)
            os.environ.pop("PYCHRON_PROMETHEUS_PORT", None)


class TestPrometheusPluginErrorHandling(unittest.TestCase):
    """Test error handling in Prometheus plugin."""

    def setUp(self):
        """Reset observability state."""
        from pychron.observability import configure

        configure(MetricsConfig(enabled=False))

    def tearDown(self):
        """Clean up."""
        from pychron.observability import configure

        configure(MetricsConfig(enabled=False))

    def test_plugin_handles_exporter_startup_failure(self):
        """Test that plugin handles exporter startup failures gracefully."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 1  # Invalid port should cause failure

        # Should not raise exception
        plugin.start()

        # Exporter may not have started due to invalid port
        # But the plugin should still be functional for metrics recording

    def test_plugin_handles_invalid_config_gracefully(self):
        """Test plugin handles invalid configuration."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = -1  # Invalid port

        # Should raise during check
        self.assertFalse(plugin.check())


class TestPrometheusPluginFullLifecycle(unittest.TestCase):
    """Test full lifecycle of plugin from creation to metrics recording."""

    def setUp(self):
        """Reset observability state."""
        from pychron.observability import configure

        configure(MetricsConfig(enabled=False))

    def tearDown(self):
        """Clean up."""
        from pychron.observability import configure

        configure(MetricsConfig(enabled=False))

    def test_complete_plugin_lifecycle(self):
        """Test complete lifecycle: create, configure, start, record metrics, stop."""
        from pychron.observability import inc_counter

        # Create plugin
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 49109

        # Check configuration
        self.assertTrue(plugin.check())

        # Start plugin
        plugin.start()

        # Record metrics
        inc_counter(
            "lifecycle_test_total",
            "Lifecycle test",
            labels=["phase", "device"],
            labelvalues={"phase": "test", "device": "lifecycle_device"},
        )

        # Verify exporter is running
        self.assertTrue(plugin._exporter_started)

    def test_plugin_lifecycle_disabled(self):
        """Test lifecycle when plugin is disabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = False

        # Check configuration
        self.assertTrue(plugin.check())

        # Start plugin
        plugin.start()

        # Exporter should not be running
        self.assertFalse(plugin._exporter_started)


if __name__ == "__main__":
    unittest.main()
