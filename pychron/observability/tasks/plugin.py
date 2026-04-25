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

"""Prometheus observability plugin for Pychron.

Provides Prometheus metrics export for monitoring experiment execution,
device I/O, and service health.
"""

from apptools.preferences.preference_binding import bind_preference
from envisage.plugin import Plugin
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import Bool, Int, Str, List

from pychron.envisage.tasks.base_plugin import BasePlugin


class PrometheusPlugin(BasePlugin):
    """Plugin for Prometheus metrics export.

    Provides HTTP endpoint for Prometheus metrics scraping and
    instruments key experiment lifecycle events.
    """

    id = "pychron.observability.prometheus"
    name = "Prometheus Observability"

    # Configuration traits
    enabled = Bool(False, help="Enable Prometheus metrics export")
    host = Str("127.0.0.1", help="Host to bind metrics HTTP server to")
    port = Int(9109, help="Port to bind metrics HTTP server to")
    namespace = Str("pychron", help="Prometheus metric namespace prefix")

    # Preferences pane contribution
    preferences_panes = List(contributes_to="envisage.ui.tasks.preferences_panes")

    # Task contribution
    tasks = List(contributes_to="envisage.ui.tasks.tasks")

    def _tasks_default(self):
        """Provide Prometheus observability task."""
        from pychron.observability.tasks.task import PrometheusObservabilityTask

        return [
            TaskFactory(
                id="pychron.observability.prometheus_task",
                name="Prometheus Observability",
                factory=PrometheusObservabilityTask,
            )
        ]

    def _preferences_panes_default(self):
        """Provide Prometheus preferences pane factory."""
        from pychron.observability.tasks.preferences_pane import (
            PrometheusPreferencesPane,
        )

        # Return class, not instance - Envisage will instantiate it
        return [PrometheusPreferencesPane]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._exporter_started = False

    def start(self) -> None:
        """Start the plugin and initialize Prometheus exporter."""
        super().start()
        self.debug("Starting Prometheus plugin")

        # Initialize event capture for UI
        self._initialize_event_capture()

        # Bind traits to preferences for automatic synchronization
        self._bind_preferences()

        # Configure observability
        self._configure_observability()

        # Start exporter if enabled
        if self.enabled:
            self._start_exporter()

    def _initialize_event_capture(self) -> None:
        """Initialize event capture system for observability UI."""
        try:
            from pychron.observability import event_capture

            # Enable event capture
            event_capture.set_capture_enabled(True)
            self.debug("Event capture initialized")
        except Exception as e:
            self.warning(f"Error initializing event capture: {e}")

    def _bind_preferences(self) -> None:
        """Bind plugin traits to preferences system."""
        try:
            from pychron.observability.tasks.preferences_pane import (
                PrometheusPreferences,
            )

            # Get preferences helper instance to read current values
            prefs_helper = PrometheusPreferences(preferences=self.application.preferences)

            # Update plugin traits from preferences
            self.enabled = prefs_helper.enabled
            self.host = prefs_helper.host
            self.port = prefs_helper.port
            self.namespace = prefs_helper.namespace

            self.debug(
                f"Loaded preferences: enabled={self.enabled}, host={self.host}, "
                f"port={self.port}, namespace={self.namespace}"
            )

            # Bind traits to preferences for future changes
            for trait_name in ("enabled", "host", "port", "namespace"):
                bind_preference(
                    self,
                    trait_name,
                    f"pychron.observability.{trait_name}",
                    preferences=self.application.preferences,
                )
        except Exception as e:
            self.warning(f"Error binding preferences: {e}")
            self.debug("Using default configuration")

    def _configure_observability(self) -> None:
        """Configure the observability system with current settings."""
        from pychron.observability import configure, MetricsConfig

        config = MetricsConfig(
            enabled=self.enabled,
            host=self.host,
            port=self.port,
            namespace=self.namespace,
        )
        configure(config)

        self.debug(
            f"Configured observability: enabled={self.enabled}, "
            f"host={self.host}, port={self.port}, namespace={self.namespace}"
        )

    def _start_exporter(self) -> None:
        """Start the HTTP metrics exporter."""
        if self._exporter_started:
            return

        try:
            from pychron.observability.exporter import start_exporter

            if start_exporter():
                self._exporter_started = True
                self.debug(
                    f"Prometheus metrics exporter started on {self.host}:{self.port}/metrics"
                )
            else:
                self.warning("Failed to start Prometheus metrics exporter")
        except Exception as e:
            self.warning(f"Error starting Prometheus exporter: {e}")

    def check(self) -> bool:
        """Verify plugin is properly configured.

        Returns:
            True if plugin is ready to use.
        """
        if not self.enabled:
            return True

        # Check that port is valid
        if self.port < 1 or self.port > 65535:
            self.warning(f"Invalid port number: {self.port}")
            return False

        return True


# ============= EOF =============================================
