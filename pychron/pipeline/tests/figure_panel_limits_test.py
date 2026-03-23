import unittest

from pychron.options.aux_plot import AuxPlot
from pychron.pipeline.plot.panels.figure_panel import FigurePanel


class DummyFigure:
    suppress_xlimits_update = False
    suppress_ylimits_update = False


class DummyPlot:
    def __init__(self):
        self.value_scale = "linear"


class DummyGraph:
    def __init__(self, n):
        self.plots = [DummyPlot() for _ in range(n)]
        self.y_limit_calls = []
        self.x_limit_calls = []

    def set_y_limits(self, *args, **kw):
        self.y_limit_calls.append((args, kw))

    def set_x_limits(self, *args, **kw):
        self.x_limit_calls.append((args, kw))


class DummyOptions:
    xpadding = "0.1"


class FigurePanelLimitTestCase(unittest.TestCase):
    def setUp(self):
        self.panel = FigurePanel(plot_options=DummyOptions(), graph_id=0)
        self.panel.figures = [DummyFigure()]

    def test_manual_xlimits_preferred_over_auto(self):
        manual = AuxPlot()
        manual.xlimits = (10, 20)
        manual._has_xlimits = True

        auto = AuxPlot()
        auto.xlimits = (1, 99)

        self.assertEqual(self.panel._get_manual_xlimits([manual, auto]), (10, 20))

    def test_calculated_ylimits_used_when_no_manual_limits(self):
        plot = AuxPlot()
        plot.calculated_ymin[0] = 2
        plot.calculated_ymax[0] = 8

        self.assertEqual(self.panel._get_plot_y_limits(plot), (2, 8))

    def test_apply_plot_limits_suppresses_limit_feedback(self):
        plot = AuxPlot()
        plot.calculated_ymin[0] = 2
        plot.calculated_ymax[0] = 8
        graph = DummyGraph(1)

        self.panel._apply_plot_limits(graph, [plot], (0, 10), None)

        self.assertFalse(self.panel.figures[0].suppress_xlimits_update)
        self.assertFalse(self.panel.figures[0].suppress_ylimits_update)
        self.assertEqual(len(graph.y_limit_calls), 1)
        self.assertEqual(len(graph.x_limit_calls), 1)
        self.assertFalse(graph.y_limit_calls[0][1]["force"])
        self.assertFalse(graph.x_limit_calls[0][1]["force"])


if __name__ == "__main__":
    unittest.main()
