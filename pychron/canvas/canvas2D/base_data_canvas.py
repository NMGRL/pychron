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
from traits.api import Tuple, Bool, on_trait_change
from enable.api import Pointer
from chaco.api import LinePlot, LinearMapper, DataView, ArrayDataSource
from chaco.tools.api import ZoomTool, PanTool
# =============standard library imports ========================
from numpy import hstack
# =============local library imports  ==========================


class BaseDataCanvas(DataView):
    """
    """
    # fill_padding = True
    #    bgcolor = (0.9, 0.9, 1.0)
    #    bgcolor = (0, 1.0, 0)
    #    border_visible = True
    # use_backbuffer = True
    #    bgcolor = 'lightblue'
    unified_draw = True
    x_range = Tuple
    y_range = Tuple
    view_x_range = Tuple
    view_y_range = Tuple
    select_pointer = Pointer('hand')
    normal_pointer = Pointer('arrow')
    cross_pointer = Pointer('cross')

    show_axes = Bool(True)
    show_grids = Bool(True)
    use_zoom = Bool(True)
    use_pan = Bool(True)

    plot = None

    def cmap_plot(self, z):
        from chaco.array_plot_data import ArrayPlotData
        from chaco.plot import Plot
        from chaco.default_colormaps import color_map_name_dict

        pd = ArrayPlotData()
        pd.set_data('cmapdata', z)

        p = Plot(pd, padding=0)
        p.img_plot('cmapdata',
                   xbounds=(-25, 25),
                   ybounds=(-25, 25),
                   colormap=color_map_name_dict['hot'])
        self.add(p)
        return pd

    def line_plot(self, x, y, new_plot=True):
        if self.plot is None or new_plot:
            if isinstance(x, (float, int)):
                x = [x]

            if isinstance(y, (float, int)):
                y = [y]

            self.plot = LinePlot(
                index=ArrayDataSource(x),
                value=ArrayDataSource(y),
                index_mapper=LinearMapper(range=self.index_range),
                value_mapper=LinearMapper(range=self.value_range))

            self.add(self.plot)
        else:

            datax = self.plot.index.get_data()
            datay = self.plot.value.get_data()
            nx = hstack((datax, [x]))
            ny = hstack((datay, [y]))

            self.plot.index.set_data(nx)
            self.plot.value.set_data(ny)

    def reset_plots(self):
        self.plot = None
        for c in self.components[:1]:
            self.remove(c)
        self.request_redraw()

    def __init__(self, *args, **kw):
        """

        """
        super(BaseDataCanvas, self).__init__(*args, **kw)
        if 'x_range' not in kw:
            self.x_range = (-25, 25)

        if 'y_range' not in kw:
            self.y_range = (-25, 25)

        if 'view_x_range' not in kw:
            self.view_x_range = (-25, 25)

        if 'view_y_range' not in kw:
            self.view_y_range = (-25, 25)

        # plot=BaseXYPlot
        plot = LinePlot

        sp = plot(index=ArrayDataSource(self.y_range),
                  value=ArrayDataSource(self.x_range),
                  index_mapper=LinearMapper(range=self.index_range),
                  value_mapper=LinearMapper(range=self.value_range))

        self.index_range.sources.append(sp.index)
        self.value_range.sources.append(sp.value)

        sp.visible = False
        self.add(sp)
        if self.use_zoom:
            self.add_zoom()

        if self.use_pan:
            self.add_pan()

        self.index_mapper.on_trait_change(self.update, 'updated')
        self.value_mapper.on_trait_change(self.update, 'updated')

        # set the view range
        self.set_mapper_limits('x', self.view_x_range)
        self.set_mapper_limits('y', self.view_y_range)

        #        if not self.show_axes:
        #            self.value_axis.visible = False
        #            self.index_axis.visible = False
        self.value_axis.visible = self.show_axes
        self.index_axis.visible = self.show_axes

        self.x_grid.visible = self.show_grids
        self.y_grid.visible = self.show_grids

    @on_trait_change('view_x_range')
    def _update_xrange(self):
        self.set_mapper_limits('x', self.view_x_range)

    @on_trait_change('view_y_range')
    def _update_yrange(self):
        self.set_mapper_limits('y', self.view_y_range)

    @on_trait_change('show_grids')
    def change_grid_visibility(self):
        print 'change visiblity', self.show_grids
        try:

            self.x_grid.visible = self.show_grids
            self.y_grid.visible = self.show_grids
            self.request_redraw()
        except AttributeError:
            pass

    def set_mapper_limits(self, mapper, limits, pad=0):
        """
        """
        mapper = getattr(self, '{}_mapper'.format(mapper))
        if mapper is not None:
            mapper.range.low_setting = limits[0] - pad
            mapper.range.high_setting = limits[1] + pad
            self.request_redraw()

    def get_mapper_limits(self, mapper):
        mapper = getattr(self, '{}_mapper'.format(mapper))
        return mapper.range.low, mapper.range.high

    def update(self, *args, **kw):
        """

        """
        pass

    def add_pan(self):
        """
        """
        p = PanTool(self)
        self.tools.append(p)

    def add_zoom(self):
        """
        """
        z = ZoomTool(component=self, always_on=False, tool_mode='box',
                     max_zoom_out_factor=1,
                     max_zoom_in_factor=10000)

        # b=BroadcasterTool()
        # b.tools.append(z)
        self.overlays.append(z)

        # self.tools.append(b)

    def get_wh(self, *args):
        return self._get_wh(*args)

    def _get_wh(self, w, h):
        """

        """
        wh, oo = self.map_screen([(w, h), (0, 0)])
        w = wh[0] - oo[0]
        h = wh[1] - oo[1]

        return w, h

    def _vertical_line(self, gc, x, y1, y2, color=(0, 0, 0)):
        """
        """

        p1 = (x, y1)
        p2 = (x, y2)
        self.line_segment(gc, p1, p2, color)

    def _horizontal_line(self, gc, y, x1, x2, color=(0, 0, 0)):
        """
        """
        p1 = (x1, y)
        p2 = (x2, y)
        self.line_segment(gc, p1, p2, color)

    def _line_segment(self, gc, p1, p2, color=None):
        if color is not None:
            gc.set_stroke_color(color)

        gc.move_to(*p1)
        gc.line_to(*p2)
        gc.draw_path()

        # def _draw_underlay(self, gc, *args, **kw):
        #     """
        #     """
        #     pass
        #
        # def _draw_underlay(self, *args, **kw):
        #     super(BaseDataCanvas, self)._draw_underlay(*args, **kw)
        #     self._draw_hook(*args, **kw)

        # def draw(self, *args, **kw):
        #     """
        #     """
        #
        #     super(BaseDataCanvas, self).draw(*args, **kw)
        #     self._draw_hook(*args, **kw)

# ====================EOF==================
