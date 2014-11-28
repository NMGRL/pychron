# ===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================
from chaco.api import PlotGrid, BarPlot, ArrayDataSource, \
    DataRange1D, LinearMapper, add_default_axes

#=============standard library imports ========================

#=============local library imports  ==========================
from regression_graph import RegressionGraph
from pychron.graph.guide_overlay import GuideOverlay


class ResidualsGraph(RegressionGraph):
    '''
    '''
    xtitle = None

    def _plotcontainer_default(self):
        '''
        '''
        return self.container_factory()

    def container_factory(self):
        '''
        '''
        kw = {'type': 'v', 'stack_order': 'top_to_bottom'}
        for k, v in self.container_dict.iteritems():
            kw[k] = v
        return self._container_factory(**kw)

    def _metadata_changed(self, obj, name, new):
        '''
        '''
        super(ResidualsGraph, self)._metadata_changed(obj, name, new)
        self.update_residuals()

    def update_residuals(self):
        '''
        '''
        x, _y, res = self.calc_residuals()
        if x is not None:
            args = self._split_residual(x, res)
            for p, i, v in [(0, 0, 1), (1, 2, 3)]:
                plot = self.residual_plots[p]

                plot.index.set_data(args[i])
                plot.value.set_data(args[v])

    def _split_residual(self, x, res):
        '''
        '''
        resneg = []
        respos = []
        xneg = []
        xpos = []
        for i, ri in enumerate(res):
            if ri <= 0:
                xneg.append(x[i])
                resneg.append(ri)
            else:
                xpos.append(x[i])
                respos.append(ri)

        return xneg, resneg, xpos, respos

    def add_datum(self, *args, **kw):
        '''
        '''
        super(ResidualsGraph, self).add_datum(*args, **kw)
        self.update_residuals()

    def new_plot(self, *args, **kw):
        self.xtitle = kw['xtitle'] if 'xtitle' in kw else None
        return super(ResidualsGraph, self).new_plot(*args, **kw)

    def new_series(self, x=None, y=None, plotid=0, **kw):
        '''
        '''

        plot, scatter, _line = super(ResidualsGraph, self).new_series(x=x, y=y, plotid=plotid, **kw)
        for underlay in plot.underlays:
            if underlay.orientation == 'bottom':
                underlay.visible = False
                underlay.padding_bottom = 0
        plot.padding_bottom = 0

        x, y, res = self.calc_residuals(plotid=plotid)

        ressplit = self._split_residual(x, res)
        resneg = ArrayDataSource(ressplit[1])
        xneg = ArrayDataSource(ressplit[0])
        respos = ArrayDataSource(ressplit[3])
        xpos = ArrayDataSource(ressplit[2])

        yrange = DataRange1D(ArrayDataSource(res))

        ymapper = LinearMapper(range=yrange)

        container = self._container_factory(type='o',
                                            padding=[50, 15, 0, 30],
                                            height=75,
                                            resizable='h'
                                            )
        bar = BarPlot(index=xneg,
                    value=resneg,
                    index_mapper=scatter.index_mapper,
                    value_mapper=ymapper,
                    bar_width=0.2,
                    line_color='blue',
                    fill_color='blue',

                    border_visible=True,
                    )

#        left_axis = PlotAxis(bar, orientation = 'left')
        # bottom_axis=PlotAxis(bar,orientaiton='bottom')

        kw = dict(vtitle='residuals')
        if self.xtitle:
            kw['htitle'] = self.xtitle
        add_default_axes(bar, **kw)
        hgrid = PlotGrid(mapper=ymapper,
                       component=bar,
                       orientation='horizontal',
                       line_color='lightgray',
                       line_style='dot')

        bar.underlays.append(hgrid)
#        bar.underlays.append(left_axis)
#        bar.underlays.append(bottom_axis)

        bar2 = BarPlot(index=xpos,
                    value=respos,
                    index_mapper=scatter.index_mapper,
                    value_mapper=ymapper,
                    bar_width=0.2,
                    line_color='green',
                    fill_color='green',
                    # bgcolor = 'green',

                    resizable='hv',
                    border_visible=True,
                    # padding = [30, 5, 0, 30]
                    )
        bar2.overlays.append(GuideOverlay(bar2, value=0, color=(0, 0, 0)))
        bar2.underlays.append(hgrid)
        container.add(bar)
        container.add(bar2)

        # container.add(PlotLabel('foo'))

        self.residual_plots = [bar, bar2]
        self.plotcontainer.add(container)
#============= EOF =====================================
