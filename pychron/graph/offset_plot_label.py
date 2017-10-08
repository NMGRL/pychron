from chaco.plot_label import PlotLabel
from traits.api import Int


class OffsetPlotLabel(PlotLabel):
    x_offset = Int
    y_offset = Int

    def _layout_as_overlay(self, size=None, force=False):
        """ Lays out the label as an overlay on another component.
        """
        super(OffsetPlotLabel, self)._layout_as_overlay()
        self.x += self.x_offset
        self.y += self.y_offset

        return
