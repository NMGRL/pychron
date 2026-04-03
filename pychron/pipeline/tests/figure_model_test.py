import unittest

from traits.api import HasTraits, Any, Int, List, Str

from pychron.pipeline.plot.models.figure_model import FigureModel


class DummyFigure:
    def __init__(self, analyses):
        self.analyses = analyses
        self.options = None
        self.graph_id = 0
        self.replot_count = 0

    def replot(self):
        self.replot_count += 1


class DummyPanel(HasTraits):
    analyses = Any
    plot_options = Any
    graph_id = Int
    references = List
    title = Str
    figures = List
    make_graph_count = Int

    def make_figures(self):
        self.figures = [DummyFigure(list(self.analyses))]

    def make_graph(self):
        self.make_graph_count += 1
        if not self.figures:
            self.make_figures()

    def dump_metadata(self):
        return {}

    def load_metadata(self, metadata):
        pass


class DummyOptions:
    auto_generate_title = False

    @staticmethod
    def generate_title(analyses, index):
        return "Panel {}".format(index)


class DummyAnalysis:
    def __init__(self, identifier, graph_id, group_id):
        self.identifier = identifier
        self.graph_id = graph_id
        self.group_id = group_id


class DummyFigureModel(FigureModel):
    _panel_klass = DummyPanel


class FigureModelRefreshTestCase(unittest.TestCase):
    def _analysis(self, identifier, graph_id=0, group_id=0):
        return DummyAnalysis(identifier, graph_id, group_id)

    def test_refresh_reuses_panels_when_topology_is_same(self):
        model = DummyFigureModel(plot_options=DummyOptions())
        model.analyses = [self._analysis("a"), self._analysis("b")]
        self.assertTrue(model.refresh(force=True))

        panel = model.panels[0]
        figure = panel.figures[0]
        self.assertEqual(panel.make_graph_count, 1)
        self.assertEqual(figure.replot_count, 1)

        model.analyses = [self._analysis("c"), self._analysis("d")]
        self.assertFalse(model.refresh())

        self.assertIs(model.panels[0], panel)
        self.assertIs(model.panels[0].figures[0], figure)
        self.assertEqual(model.panels[0].figures[0].analyses[0].identifier, "c")
        self.assertEqual(panel.make_graph_count, 1)
        self.assertEqual(figure.replot_count, 2)

    def test_refresh_rebuilds_panels_when_topology_changes(self):
        model = DummyFigureModel(plot_options=DummyOptions())
        model.analyses = [self._analysis("a", graph_id=0)]
        self.assertTrue(model.refresh(force=True))

        panel = model.panels[0]

        model.analyses = [
            self._analysis("a", graph_id=0),
            self._analysis("b", graph_id=1),
        ]
        self.assertTrue(model.refresh())

        self.assertEqual(len(model.panels), 2)
        self.assertIsNot(model.panels[0], panel)

    def test_force_refresh_rebuilds_panels_even_when_topology_is_same(self):
        model = DummyFigureModel(plot_options=DummyOptions())
        model.analyses = [self._analysis("a"), self._analysis("b")]
        model.refresh(force=True)

        panel = model.panels[0]

        model.analyses = [self._analysis("c"), self._analysis("d")]
        self.assertTrue(model.refresh(force=True))
        self.assertIsNot(model.panels[0], panel)


if __name__ == "__main__":
    unittest.main()
