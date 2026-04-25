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

"""Tests for Prometheus initialization integration."""

import unittest
from unittest.mock import Mock, patch

from pychron.observability import MetricsConfig, configure
from pychron.observability.tasks.plugin import PrometheusPlugin
from pychron.observability.tasks.preferences_pane import (
    PrometheusPreferences,
    PrometheusPreferencesPane,
)


class TestPrometheusInitialization(unittest.TestCase):
    """Test Prometheus initialization through plugin system."""

    def setUp(self):
        """Reset metrics before each test."""
        configure(MetricsConfig(enabled=False))

    def tearDown(self):
        """Clean up after tests."""
        configure(MetricsConfig(enabled=False))

    def test_prometheus_plugin_creation(self):
        """Test PrometheusPlugin can be instantiated."""
        plugin = PrometheusPlugin()
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "pychron.observability.prometheus")
        self.assertEqual(plugin.name, "Prometheus Observability")

    def test_prometheus_plugin_defaults(self):
        """Test PrometheusPlugin has correct default values."""
        plugin = PrometheusPlugin()
        self.assertFalse(plugin.enabled)
        self.assertEqual(plugin.host, "127.0.0.1")
        self.assertEqual(plugin.port, 9109)
        self.assertEqual(plugin.namespace, "pychron")

    def test_prometheus_preferences_model(self):
        """Test PrometheusPreferences model."""
        prefs = PrometheusPreferences()
        self.assertFalse(prefs.enabled)
        self.assertEqual(prefs.host, "127.0.0.1")
        self.assertEqual(prefs.port, 9109)
        self.assertEqual(prefs.namespace, "pychron")

    def test_prometheus_preferences_custom_values(self):
        """Test PrometheusPreferences with custom values."""
        prefs = PrometheusPreferences(
            enabled=True,
            host="0.0.0.0",
            port=8888,
            namespace="custom",
        )
        self.assertTrue(prefs.enabled)
        self.assertEqual(prefs.host, "0.0.0.0")
        self.assertEqual(prefs.port, 8888)
        self.assertEqual(prefs.namespace, "custom")

    def test_prometheus_preferences_metrics_url_default(self):
        """Test PrometheusPreferences generates correct default metrics URL."""
        prefs = PrometheusPreferences()
        self.assertEqual(prefs.metrics_url, "http://127.0.0.1:9109/metrics")

    def test_prometheus_preferences_metrics_url_custom(self):
        """Test PrometheusPreferences generates correct custom metrics URL."""
        prefs = PrometheusPreferences(host="0.0.0.0", port=8888)
        self.assertEqual(prefs.metrics_url, "http://0.0.0.0:8888/metrics")

    def test_prometheus_preferences_metrics_url_dynamic(self):
        """Test PrometheusPreferences metrics URL updates dynamically."""
        prefs = PrometheusPreferences()

        # Change host
        prefs.host = "192.168.1.100"
        self.assertEqual(prefs.metrics_url, "http://192.168.1.100:9109/metrics")

        # Change port
        prefs.port = 8080
        self.assertEqual(prefs.metrics_url, "http://192.168.1.100:8080/metrics")

        # Change both
        prefs.host = "localhost"
        prefs.port = 5000
        self.assertEqual(prefs.metrics_url, "http://localhost:5000/metrics")

    def test_prometheus_preferences_pane_creation(self):
        """Test PrometheusPreferencesPane can be instantiated."""
        pane = PrometheusPreferencesPane()
        self.assertIsNotNone(pane)
        self.assertEqual(pane.category, "Prometheus")
        self.assertIsNotNone(pane.model_factory)

    def test_prometheus_preferences_pane_model(self):
        """Test PrometheusPreferencesPane has correct model factory."""
        pane = PrometheusPreferencesPane()
        self.assertEqual(pane.model_factory, PrometheusPreferences)

    def test_prometheus_preferences_pane_view(self):
        """Test PrometheusPreferencesPane creates a view."""
        pane = PrometheusPreferencesPane()
        view = pane.traits_view()
        self.assertIsNotNone(view)

    def test_plugin_configuration_flow(self):
        """Test plugin configuration flow."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.host = "192.168.1.1"
        plugin.port = 8080
        plugin.namespace = "test_ns"

        # Configure plugin
        plugin._configure_observability()

        # Verify configuration was applied to observability system
        from pychron.observability import get_config

        config = get_config()
        self.assertTrue(config.enabled)
        self.assertEqual(config.host, "192.168.1.1")
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.namespace, "test_ns")

    def test_plugin_validation_enabled(self):
        """Test plugin validation when enabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 9109

        # Should pass validation
        self.assertTrue(plugin.check())

    def test_plugin_validation_invalid_port(self):
        """Test plugin validation with invalid port."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 99999  # Out of range

        # Should fail validation
        self.assertFalse(plugin.check())

    def test_plugin_validation_disabled(self):
        """Test plugin validation when disabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = False
        plugin.port = 99999  # Invalid port, but plugin is disabled

        # Should pass validation (disabled plugins skip checks)
        self.assertTrue(plugin.check())

    def test_plugin_preferences_panes_default(self):
        """Test plugin provides preferences panes."""
        plugin = PrometheusPlugin()
        panes = plugin._preferences_panes_default()
        self.assertIsNotNone(panes)
        self.assertGreater(len(panes), 0)
        # Should return the class, not an instance (Envisage instantiates it)
        self.assertEqual(panes[0], PrometheusPreferencesPane)
        # Verify we can instantiate it
        pane_instance = panes[0](dialog=None)
        self.assertIsInstance(pane_instance, PrometheusPreferencesPane)

    def test_plugin_start_disabled(self):
        """Test plugin start when disabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = False

        # Should not raise exception
        plugin.start()

        # Exporter should not be started
        self.assertFalse(plugin._exporter_started)

    def test_plugin_start_enabled(self):
        """Test plugin start when enabled."""
        plugin = PrometheusPlugin()
        plugin.enabled = True
        plugin.port = 19109  # Use high port

        try:
            plugin.start()
            # Should have attempted to start exporter
            self.assertTrue(plugin._exporter_started)
        finally:
            # Clean up
            configure(MetricsConfig(enabled=False))


class TestPrometheusInitializationUtilities(unittest.TestCase):
    """Test Prometheus integration in initialization utilities."""

    def test_prometheus_in_description_map(self):
        """Test Prometheus is in DESCRIPTION_MAP."""
        from pychron.envisage.initialization.utilities import DESCRIPTION_MAP

        self.assertIn("Prometheus", DESCRIPTION_MAP)
        self.assertIn("metrics", DESCRIPTION_MAP["Prometheus"].lower())

    def test_prometheus_in_default_plugins(self):
        """Test Prometheus is in DEFAULT_PLUGINS."""
        from pychron.envisage.initialization.utilities import DEFAULT_PLUGINS

        # Find General category
        general = None
        for category_name, plugins in DEFAULT_PLUGINS:
            if category_name == "General":
                general = plugins
                break

        self.assertIsNotNone(general)

        # Check Prometheus is in General plugins
        plugin_names = [p if isinstance(p, str) else p[0] for p in general]
        self.assertIn("Prometheus", plugin_names)

    def test_load_plugin_tree_includes_prometheus(self):
        """Test loading plugin tree includes Prometheus."""
        from pychron.envisage.initialization.utilities import load_plugin_tree

        tree = load_plugin_tree()
        self.assertIsNotNone(tree)

        # Find General category
        general = tree.get_subtree("General")
        self.assertIsNotNone(general)

        # Find Prometheus plugin
        prometheus = None
        for plugin in general.plugins:
            if plugin.name == "Prometheus":
                prometheus = plugin
                break

        self.assertIsNotNone(prometheus)


class TestPrometheusPortValidation(unittest.TestCase):
    """Test port validation in Prometheus plugin."""

    def test_valid_ports(self):
        """Test validation of valid port numbers."""
        valid_ports = [1, 80, 443, 8080, 9109, 65535]
        for port in valid_ports:
            plugin = PrometheusPlugin()
            plugin.enabled = True
            plugin.port = port
            self.assertTrue(plugin.check(), f"Port {port} should be valid")

    def test_invalid_ports(self):
        """Test validation of invalid port numbers."""
        invalid_ports = [-1, 0, 65536, 99999]
        for port in invalid_ports:
            plugin = PrometheusPlugin()
            plugin.enabled = True
            plugin.port = port
            self.assertFalse(plugin.check(), f"Port {port} should be invalid")

    def test_port_range_trait(self):
        """Test port trait enforces range."""
        prefs = PrometheusPreferences()
        # Should accept valid range
        prefs.port = 5000
        self.assertEqual(prefs.port, 5000)

        # Test boundary values
        prefs.port = 1
        self.assertEqual(prefs.port, 1)

        prefs.port = 65535
        self.assertEqual(prefs.port, 65535)


if __name__ == "__main__":
    unittest.main()
