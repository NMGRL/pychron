'''
Rotated PlotContainer example

use_backbuffer=True is critical. Python crashes otherwise.
rotate_ctm is the cause, other transforms (at least translate) work fine

'''

# ============= enthought library imports =======================
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'
from traits.api import HasTraits, Instance, Float
from traitsui.api import View, Controller, UItem
from chaco.api import OverlayPlotContainer
from enable.component_editor import ComponentEditor
from chaco.plot import Plot
from chaco.array_plot_data import ArrayPlotData

# ============= standard library imports ========================
from numpy import linspace, cos, pi
import math

# ============= local library imports  ==========================

class RotatingContainer(OverlayPlotContainer):
    rotation = Float(45)
#     use_backbuffer = True
    def draw(self, gc, *args, **kw):
        with gc:
            w2 = self.width / 2
            h2 = self.height / 2
            gc.translate_ctm(w2, h2)
            gc.rotate_ctm(math.radians(self.rotation))
            gc.translate_ctm(-w2, -h2 - 100)
            OverlayPlotContainer.draw(self, gc, *args, **kw)

class GraphicGeneratorController(Controller):

    def traits_view(self):
        v = View(
                 UItem('container', editor=ComponentEditor(),
                       style='custom'),
                 width=500,
                 height=500,
                 resizable=True,
                 )
        return v

class GraphicModel(HasTraits):
    container = Instance(OverlayPlotContainer)
    def load(self):
        data = ArrayPlotData()
        p = Plot(data=data, padding=100)
        X = linspace(0, 2 * pi)
        data.set_data('x0', X)
        data.set_data('y0', cos(X))

        p.plot(('x0', 'y0'))
        self.container.add(p)

    def _container_default(self):
        c = RotatingContainer(bgcolor='white')
        return c


if __name__ == '__main__':
    gm = GraphicModel()
    gm.load()
    gcc = GraphicGeneratorController(model=gm)

    gcc.configure_traits()

# ============= EOF =============================================
