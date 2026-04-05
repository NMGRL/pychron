"""Prometheus observability task for displaying metrics and events."""

from traits.api import Property, Int, Str, Bool
from traitsui.api import View

from pychron.envisage.tasks.base_task import BaseTask


class PrometheusObservabilityTask(BaseTask):
    """Task for displaying Prometheus metrics and event logs.

    Provides a comprehensive UI for:
    - Connection status and configuration
    - Real-time metrics preview
    - Event audit log
    - Control buttons (enable/disable, export, clear)
    """

    id = "pychron.observability.prometheus_task"
    name = "Prometheus Observability"

    # Task window configuration
    window_width = Int(1200)
    window_height = Int(800)

    def create_central_pane(self):
        """Create the central pane for this task."""
        from pychron.observability.tasks.panes.status_pane import (
            PrometheusStatusPane,
        )

        return PrometheusStatusPane()

    def create_dock_panes(self):
        """Create dock panes for this task."""
        from pychron.observability.tasks.panes.event_pane import (
            PrometheusEventPane,
        )

        return [PrometheusEventPane()]

    def traits_view(self):
        """Return the view for this task (not typically used for task panes)."""
        return View()
