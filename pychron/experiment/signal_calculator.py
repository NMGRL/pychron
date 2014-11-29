# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Float, on_trait_change, Instance, Enum, \
    String
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor
# ============= standard library imports ========================
import numpy as np
import math
# ============= local library imports  ==========================
from pychron.processing.arar_constants import ArArConstants
from pychron.graph.graph import Graph
# from chaco.axis import PlotAxis
# from chaco.plot_factory import create_line_plot, add_default_axes
# from pychron.graph.guide_overlay import GuideOverlay

powerlaw = lambda pp, x: pp[0] * x ** pp[1]

class Index(HasTraits):
    name = Str
    start = Float(0)
    end = Float(0.25)
    r4039 = Float(8)

    def calculate(self, age, sensitivity, k2o):
        c = ArArConstants()
        xs = np.linspace(self.start, self.end)
        ys = np.array([self._calculate(wi, age, sensitivity, k2o, c) for wi in xs])


#        nxs = np.linspace(max(1e-2, 0), self.end)
#        n40 = np.linspace(max(1, ys[0]), ys[-1])
        n40 = ys[:]
        if ys[0] == 0:
            n40 = n40[1:]

#        r4039 = 7.78
        n39 = n40 / self.r4039
#        nys = ys[:]
#        print nys
#            nys = np.hstack(([1], nys[1:]))
#        print nys
        p = (0.0021435788651550671, -0.48505328994128016)
        e40_scalar = 3
        e39 = powerlaw(p, n39)
        e40 = powerlaw(p, n40) * e40_scalar

        es = (e39 ** 2 + e40 ** 2) ** 0.5
#        es = age * 1e3 * es
#        es = 0.2 * nys ** (-0.5)

        return xs, ys, n40, es * 100

    def _calculate(self, w, age, sensitivity, k2o, c):
        moles_40k = w / 1000. *k2o / 100. * 1 / c.mK * (2 * c.mK) / (2 * c.mK + c.mO) * c.abundance_40K
        moles_40Ar = moles_40k * (math.exp(c.lambda_k.nominal_value * age * 1e6) - 1) * (c.lambda_e_v / c.lambda_k.nominal_value)
        return moles_40Ar / sensitivity


class WeightIndex(Index):
    name = 'Weight'
    def traits_view(self):
        v = View(Item('start', label='Weight Start (mg)'),
#                        spring,
                 Item('end', label='Weight End (mg)'))
        return v

class VolumeIndex(Index):
    name = 'Volume'
    depth = Float(0.1)  # mm
    rho = 2580  # kg/m^3
    shape = Enum('circle', 'square')
    def traits_view(self):
        v = View(Item('start', label='Dimension Start (mm)'),
                 Item('end', label='Dimension End (mm)'),
                 HGroup(Item('shape'), Item('depth', label='Depth (mm)')),
                 )
        return v

    def calculate(self, age, sensitivity, k2o):
        c = ArArConstants()
        xs = np.linspace(self.start, self.end)

        def to_weight(d, depth, rho):
            '''
                d== mm
                depth==mm
                rho==kg/m^3
            '''
            # convert dimension to meters
            d = d / 1000.
            depth = depth / 1000.
            if self.shape == 'circle':
                v = math.pi * (d / 2.) ** 2 * depth
            else:
                v = d ** 2 * depth

            m = rho * v
            # convert mass to mg 1e6 mg in 1 kg
            return m * 1e6

        # convert dim to weight
        ws = [to_weight(di, self.depth, self.rho) for di in xs]

        ys = [self._calculate(wi, age, sensitivity, k2o, c) for wi in ws]
        return xs, ys, xs, ws

    def _shape_default(self):
        return 'circle'

class IndexSelector(HasTraits):
    name = String('Weight')
    names = ['Volume', 'Weight']
    def traits_view(self):
        v = View(Item('name', editor=EnumEditor(name='names')))
        return v

class SignalCalculator(HasTraits):
    age = Float(28.2)
    k2o = Float  # percent
    sensitivity = Float(5e-17)  # moles/fA
    r4039 = Float(8)

    graph = Instance(Graph)
#    weight_index = Instance(WeightIndex, ())
#    volume_index = Instance(VolumeIndex, ())
#    kind = Enum('weight', 'volume')
    x = Instance(IndexSelector, ())
    y = Instance(IndexSelector)

#    def _kind_changed(self):
#        if self.kind == 'weight':
#            self.secondary_plot.visible = False
#        else:
#            self.secondary_plot.visible = True
#
#        self._calculate()

    index = Instance(Index)
    def _r4039_changed(self):
        self.index.r4039 = self.r4039

    @on_trait_change('x:name')
    def _update_index_kind(self):
        if self.x.name == 'Weight':
            self.index = WeightIndex()
        else:
            self.index = VolumeIndex()

    @on_trait_change('index:+, index:+, sensitivity, k2o, age')
    def _calculate(self):
        '''
            calculate signal size for n mg of sample with m k2o of age p 
        '''
        if self.x.name == 'weight':
#            attr = self.weight_index
            self.graph.set_x_title('weight (mg)')
        else:
            self.graph.set_x_title('dimension (mm)')
#            attr = self.volume_index

        xs, ys, xx, yy = self.index.calculate(self.age, self.sensitivity, self.k2o)
        self.graph.set_data(xs)
        self.graph.set_data(ys, axis=1)

        self.graph.set_data(xx, plotid=1)
        self.graph.set_data(yy, plotid=1, axis=1)
#        self.secondary_plot.index.set_data(xx)
#        self.secondary_plot.value.set_data(yy)

        self.graph.redraw()

    def traits_view(self):
        cntrl_grp = VGroup(
                           Item('age', label='Age (Ma)'),
                           HGroup(Item('k2o', label='K2O %'),
                                  Item('r4039', label='(Ar40*/Ar39K)std'),
#                                  spring,
                                  Item('sensitivity', label='Sensitivity (mol/fA)')),

                            Item('x', style='custom', show_label=False),
                            Item('index', style='custom', show_label=False),
#                           Item('kind'),
#                           Item('volume_index', show_label=False, style='custom',
#                                visible_when='kind=="volume"'),
#                           Item('weight_index', show_label=False, style='custom',
#                                visible_when='kind=="weight"'),

                           )

        graph_grp = VGroup(Item('graph',
                                width=800,
                                height=500,
                                show_label=False, style='custom'),)
        v = View(
                 VGroup(cntrl_grp, graph_grp),
                 resizable=True,
                 title='Signal Calculator'
                 )
        return v


    def _graph_default(self):
        g = Graph(container_dict=dict(padding=5,

                                      kind='h'))
        g.new_plot(xtitle='weight (mg)', ytitle='40Ar* (fA)',
                   padding=[60, 20, 60, 60]
#                   padding=60
                   )

        g.new_series()
        g.new_plot(xtitle='40Ar* (fA)', ytitle='%Error in Age',
                   padding=[30, 30, 60, 60]
                   )
        g.new_series()
#        fp = create_line_plot(([], []), color='red')
#        left, bottom = add_default_axes(fp)
#        bottom.visible = False
#        left.orientation = 'right'
#        left.axis_line_visible = False
#        bottom.axis_line_visible = False
#        left.visible = False

#        if self.kind == 'weight':
#            bottom.visible = True
#            bottom.orientation = 'top'
#            bottom.title = 'Error (ka)'
#            bottom.tick_color = 'red'
#            bottom.tick_label_color = 'red'
#            bottom.line_color = 'red'
#            bottom.title_color = 'red'
#        else:
#            left.title = 'Weight (mg)'
#        fp.visible = False
#        gd = GuideOverlay(fp, value=0.01, orientation='v')
#        fp.overlays.append(gd)
#        g.plots[0].add(fp)
#        self.secondary_plot = fp

        return g

    def _index_default(self):
        return WeightIndex(r4039=self.r4039)
#    def _kind_default(self):
#        return 'weight'

if __name__ == '__main__':
    sc = SignalCalculator()
    sc.configure_traits()
# ============= EOF =============================================
