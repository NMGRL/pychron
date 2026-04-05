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

"""Preferences pane for Prometheus observability configuration."""

from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Bool, Str, Range, Property
from traitsui.api import VGroup, Item, Label

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class PrometheusPreferences(BasePreferencesHelper):
    """Preferences for Prometheus metrics export."""

    preferences_path = "pychron.observability"

    enabled = Bool(
        False,
        label="Enabled",
        help="Enable Prometheus metrics collection and HTTP export",
    )
    host = Str(
        "127.0.0.1",
        label="Host",
        help="Host address to bind metrics HTTP server to",
    )
    port = Range(
        low=1,
        high=65535,
        value=9109,
        label="Port",
        help="Port to bind metrics HTTP server to",
    )
    namespace = Str(
        "pychron",
        label="Namespace",
        help="Prometheus metric namespace prefix",
    )

    # Dynamic property for metrics URL
    metrics_url = Property(Str, observe="host, port")

    def _get_metrics_url(self):
        """Generate the metrics endpoint URL from host and port."""
        return f"http://{self.host}:{self.port}/metrics"


class PrometheusPreferencesPane(PreferencesPane):
    """Preferences pane for Prometheus configuration."""

    category = "Prometheus"
    model_factory = PrometheusPreferences

    def traits_view(self):
        """Build the preferences view."""
        from traitsui.api import View

        return View(
            VGroup(
                Item(
                    "enabled",
                    label="Enable Prometheus Metrics Export",
                    tooltip="Enable to start HTTP metrics server on application startup",
                ),
                VGroup(
                    Label("HTTP Server Configuration"),
                    Item(
                        "host",
                        label="Host",
                        tooltip="Hostname or IP address for metrics HTTP server",
                    ),
                    Item(
                        "port",
                        label="Port",
                        tooltip="Port number for metrics HTTP server (1-65535)",
                    ),
                    Item(
                        "namespace",
                        label="Metric Namespace",
                        tooltip="Prefix for all exported metric names",
                    ),
                    enabled_when="enabled",
                    label="Server Settings",
                ),
                VGroup(
                    Item(
                        "metrics_url",
                        style="readonly",
                        label="Metrics URL",
                        tooltip="The URL where Prometheus metrics will be exposed",
                    ),
                    Label(
                        "Configure your Prometheus instance to scrape this endpoint:\n\n"
                        "scrape_configs:\n"
                        "  - job_name: 'pychron'\n"
                        "    static_configs:\n"
                        "      - targets: ['<pychron-host>:9109']"
                    ),
                    label="Usage",
                ),
                label="Observability",
            ),
        )


# ============= EOF =============================================
