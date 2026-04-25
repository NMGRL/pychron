"""Prometheus observability task for displaying metrics and events."""

from traits.api import Property, Int, Str, Bool, Instance
from traitsui.api import View

from pychron.envisage.tasks.base_task import BaseTask
from pychron.observability.tasks.model import PrometheusObservabilityModel


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

    # Shared model
    model = Instance(PrometheusObservabilityModel)

    def __init__(self, **kw):
        """Initialize task with shared model."""
        super().__init__(**kw)
        self.model = PrometheusObservabilityModel()

    def create_central_pane(self):
        """Create the central pane for this task."""
        from pychron.observability.tasks.panes.status_pane import (
            PrometheusStatusPane,
        )

        pane = PrometheusStatusPane(model=self.model)
        return pane

    def create_dock_panes(self):
        """Create dock panes for this task."""
        from pychron.observability.tasks.panes.event_pane import (
            PrometheusEventPane,
        )

        return [PrometheusEventPane(model=self.model)]

    def traits_view(self):
        """Return the view for this task (not typically used for task panes)."""
        return View()
