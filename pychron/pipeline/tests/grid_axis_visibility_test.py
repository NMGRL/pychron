import unittest

from pychron.options.aux_plot import AuxPlot
from pychron.options.ideogram import IdeogramOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


class DummyGrid:
    def __init__(self):
        self.visible = None


class DummyRange:
    def on_trait_change(self, *args, **kw):
        pass


class DummyAxis:
    def __init__(self, title):
        self.title = title
        self.tick_visible = True
        self.tick_label_formatter = None
        self.tick_label_font = None
        self.title_font = None
        self.tick_in = None
        self.tick_out = None
        self.orientation = "left"
        self.axis_line_visible = True


class DummyValueAxis:
    def __init__(self):
        self.tick_generator = None
        self.tick_interval = None


class DummyPlot:
    def __init__(self):
        self.padding_left = 100
        self.padding_bottom = 100
        self.bgcolor = None
        self.x_grid = DummyGrid()
        self.y_grid = DummyGrid()
        self.x_axis = DummyAxis("X Axis")
        self.y_axis = DummyAxis("Y Axis")
        self.value_axis = DummyValueAxis()
        self.value_grid = DummyValueAxis()
        self.value_scale = "linear"


class DummyOptions:
    plot_bgcolor = "white"
    use_xgrid = True
    use_ygrid = True
    show_all_axes = True
    xtitle_font = "modern 12"
    ytitle_font = "modern 12"
    xtick_in = 1
    ytick_in = 1
    xtick_out = 5
    ytick_out = 5
    xtick_label_formatter = staticmethod(lambda x: "x:{}".format(x))
    ytick_label_formatter = staticmethod(lambda x: "y:{}".format(x))
    xtick_font = "modern 10"
    ytick_font = "modern 10"


class GridAxisVisibilityTestCase(unittest.TestCase):
    def setUp(self):
        self.figure = BaseArArFigure(options=DummyOptions(), group_id=1, subgroup_id=1)

    def _plot_options(self, **kw):
        po = AuxPlot()
        po.yticks_both_sides = False
        for key, value in kw.items():
            setattr(po, key, value)
        return po

    def _apply(self, po=None, row=(0, 2), col=(1, 2), show_all=False):
        self.figure.options.show_all_axes = show_all
        plot = DummyPlot()
        self.figure._apply_aux_plot_options(False, plot, po or self._plot_options(), row, col)
        return plot

    def test_default_hides_interior_x_axis_labels(self):
        plot = self._apply()

        self.assertEqual(plot.x_axis.title, "")
        self.assertFalse(plot.x_axis.tick_visible)
        self.assertEqual(plot.x_axis.tick_label_formatter(5), "")
        self.assertEqual(plot.padding_bottom, 10)

    def test_default_hides_interior_y_axis_title_and_fixed_limit_ticks(self):
        plot = self._apply(self._plot_options(ymin=0, ymax=10), row=(1, 2), col=(1, 2))

        self.assertEqual(plot.y_axis.title, "")
        self.assertEqual(plot.y_axis.tick_label_formatter(5), "")
        self.assertEqual(plot.padding_left, 50)

    def test_override_keeps_all_grid_axes_visible(self):
        plot = self._apply(self._plot_options(ymin=0, ymax=10), show_all=True)

        self.assertEqual(plot.x_axis.title, "X Axis")
        self.assertTrue(plot.x_axis.tick_visible)
        self.assertEqual(plot.x_axis.tick_label_formatter(5), "x:5")
        self.assertEqual(plot.y_axis.title, "Y Axis")
        self.assertEqual(plot.y_axis.tick_label_formatter(5), "y:5")
        self.assertEqual(plot.padding_left, 100)
        self.assertEqual(plot.padding_bottom, 100)

    def test_override_still_respects_ytitle_visibility(self):
        plot = self._apply(self._plot_options(ytitle_visible=False), show_all=True)

        self.assertEqual(plot.y_axis.title, "")

    def test_override_still_respects_ytick_visibility(self):
        plot = self._apply(self._plot_options(ytick_visible=False), show_all=True)

        self.assertFalse(plot.y_axis.tick_visible)
        self.assertEqual(plot.y_axis.tick_label_formatter(5), "")

    def test_ideogram_and_spectrum_options_expose_trait(self):
        self.assertIsNotNone(IdeogramOptions().trait("show_all_axes"))
        self.assertIsNotNone(SpectrumOptions().trait("show_all_axes"))


if __name__ == "__main__":
    unittest.main()
