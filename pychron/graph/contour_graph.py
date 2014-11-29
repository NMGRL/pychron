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



# =============enthought library imports=======================
from chaco.api import ColorBar, LinearMapper
from chaco.data_range_1d import DataRange1D
from chaco.default_colormaps import color_map_name_dict, gray
# =============standard library imports ========================
from numpy import array
# =============local library imports  ==========================
from graph import Graph
from graph import name_generator


class ContourGraph(Graph):
    line_inspectors_write_metadata = True
    editor_enabled = False

    def __init__(self, *args, **kw):
        super(ContourGraph, self).__init__(*args, **kw)
        self.zdataname_generators = [name_generator('z')]

    def new_plot(self, add=True, **kw):
        kw['add'] = add
        p = super(ContourGraph, self).new_plot(**kw)
        self.zdataname_generators.append(name_generator('z'))

        return p

    def new_series(self, x=None, y=None, z=None, colorbar=False, plotid=0, style='xy', **kw):
        plot, names, rd = self._series_factory(x, y, plotid=plotid, **kw)

        if style in ['xy', 'cmap_scatter']:

            if style == 'cmap_scatter':
                c = 'c1'
                self.series[plotid][1] += (c,)
                if z is None:
                    z = array([])

                self.plots[plotid].data.set_data(c, z)
                names += (c,)

            if style == 'xy':
                style = 'line'
            print style
            rd['type'] = style
            return plot.plot(names, **rd)

        else:

            rd['xbounds'] = (0, 1) if 'xbounds' not in kw else kw.get('xbounds')
            rd['ybounds'] = (0, 1) if 'ybounds' not in kw else kw.get('ybounds')
            cmap = 'hot' if 'cmap' not in kw else kw.get('cmap')

            rd['poly_cmap'] = color_map_name_dict.get(cmap)
            rd['colormap'] = color_map_name_dict.get(cmap)
            zname = self.zdataname_generators[plotid].next()
            plot.data.set_data(zname, z)
            contour = plot.img_plot(zname, **rd)[0]
            plot.contour_plot(zname, type='poly', **rd)

            if 'levels' in kw:
                contour.levels = kw.get('levels')

            return contour, plot

    def metadata_changed(self):
        plot = self.plots[0]
        contour_pp = plot.plots['plot0'][0]
        index = contour_pp.index
        data = contour_pp.value

        if 'selections' in index.metadata:
            x_ndx, y_ndx = index.metadata['selections']

            if x_ndx and y_ndx:
                # get horizontal data
                d1 = data.data[y_ndx, :]
                # get vertical data
                d2 = data.data[:, x_ndx]

                xdata, ydata = index.get_data()
                xdata, ydata = xdata.get_data(), ydata.get_data()

                self.set_data(xdata, plotid=1)
                self.set_data(d1, plotid=1, axis=1)

                self.set_data(ydata, plotid=2)
                self.set_data(d2, plotid=2, axis=1)

                yy = [ydata[y_ndx]]
                xx = [xdata[x_ndx]]
                v = [data.data[y_ndx, x_ndx]]

                self.set_data(xx, plotid=1, series=1)
                self.set_data(v, plotid=1, series=1, axis=1)
                self.set_data(v, plotid=1, series=1, axis=2)

                self.set_data(yy, plotid=2, series=1)
                self.set_data(v, plotid=2, series=1, axis=1)
                self.set_data(v, plotid=2, series=1, axis=2)
                self.plotcontainer.request_redraw()

    #def _plotcontainer_default(self):
    #    '''
    #    '''
    #    return self.container_factory()

    #     def container_factory(self):
    #         '''
    #         '''
    #         return self._container_factory(kind='h', spacing=10)
    def add_colorbar(self, plot=None, container=None, **kw):
        if container is None:
            container = self.plotcontainer

        colorbar = self.make_colorbar(plot, **kw)
        container.add(colorbar)

    def make_colorbar(self, plot, width=30, padding=20, orientation='v', resizable='v'):
        cm = gray(DataRange1D())
        lm = LinearMapper()
        colorbar = ColorBar(orientation=orientation,
                            resizable=resizable,
                            width=width,
                            padding=padding,
                            index_mapper=lm,
                            color_mapper=cm)

        if plot is not None:
            colorbar.trait_set(index_mapper=LinearMapper(range=plot.color_mapper.range),
                               color_mapper=plot.color_mapper,
                               plot=plot)

        return colorbar

# ============= EOF =============================================
