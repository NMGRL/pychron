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
from chaco.polygon_plot import PolygonPlot
from traits.api import HasTraits, Property, Any, Str, Int, Float, List
from traitsui.api import View, Item, VGroup, Group, \
    TextEditor, TableEditor, Handler, InstanceEditor

# =============standard library imports ========================
# =============local library imports  ==========================
from series_editor import SeriesEditor, PolygonPlotEditor
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from kiva.trait_defs.kiva_font_trait import KivaFontFunc
from pychron.graph.editors.series_editor import ContourPolyPlotEditor
# from chaco.contour_poly_plot import ContourPolyPlot
from chaco.base_2d_plot import Base2DPlot
from chaco.cmap_image_plot import CMapImagePlot
from chaco.base_contour_plot import BaseContourPlot


class PlotEditorHandler(Handler):
    def closed(self, info, is_ok):
        '''
        '''
        obj = info.object
        obj.graph.plot_editor = None


class PlotEditor(HasTraits):
    '''
    '''

    _xtitle = Str
    _ytitle = Str

    _xmin = Float(0)
    _xmax = Float(0)
    _ymin = Float(0)
    _ymax = Float(0)

    xtitle = Property(Str, depends_on='_xtitle')
    ytitle = Property(Str, depends_on='_ytitle')
    xmax = Property(Float, depends_on='_xmax')
    xmin = Property(depends_on='_xmin')
    ymax = Property(depends_on='_ymax')
    ymin = Property(depends_on='_ymin')

#    xcolor_ = Property
#    ycolor_ = Property

    graph = Any
    plot = Any
    id = Int(0)
    name = Str('Plot Editor')
    series_editors = List

    # autoupdate = DelegatesTo('graph')

    # the _prev_selected hack prevents selected from ever being set to None
    # this prevents view resizing when hiding/showing series.
    selected = Property(depends_on='_selected')
    _selected = Any
    _prev_selected = Any

    _series_editor_klass = SeriesEditor

    def __init__(self, *args, **kw):
        '''
        '''
        super(PlotEditor, self).__init__(*args, **kw)
        if self.graph:
            self._build_series_editors()

    def _get_selected(self):
        if self._selected is None:
            s = self._prev_selected
        else:
            s = self._selected
        return s

    def __selected_changed(self, old, new):
        if new is None:
            self._prev_selected = old

    def _get_plots(self):
        if self.plot:
            pplot = self.plot
#            print self.graph.plots
            self.id = self.graph.plots.index(pplot)

        elif self.graph:
            pplot = self.graph.plots[self.id]

        plots = pplot.plots
        return plots

    def _get_series_editor_kwargs(self, plot, _id, sid=None):
#        print sid
        kwargs = dict(series=plot,
                             graph=self.graph,
                             plotid=self.id,
                             id=_id,
#                             name=n
                             )
        if sid is not None:
            n = self.graph.get_series_label(plotid=self.id, series=sid)
            if n is None:
                n = sid
            kwargs['name'] = n

        return kwargs

    def _build_series_editors(self, editors=None):
        '''
        '''
        plots = self._get_plots()

        if editors is None:
            self.series_editors = []
            editors = self.series_editors

        series_filter = True if len(plots) > 10 else False

        for i, (key, plot) in enumerate(plots.iteritems()):
#        for i, key in enumerate(plots):
#            plot = plots[key][0]i
            plot = plot[0]
            if isinstance(plot, PolygonPlot):
                editor = PolygonPlotEditor
            elif isinstance(plot, (CMapImagePlot, BaseContourPlot)):
                editor = ContourPolyPlotEditor

            else:
                editor = self._series_editor_klass

            kwargs = self._get_series_editor_kwargs(plot, i, sid=key)
            if series_filter and not kwargs['name']:
                continue

            editors.append(editor(**kwargs))

        editors.sort(key=lambda x: x.id)

        if len(editors) > 20:
            self._series_editors = editors[:10]
        if plots:
            self._sync_limits(plot)

    def _sync_limits(self, plot):
        if isinstance(plot, Base2DPlot):
            plow = plot.index_range.low
            phigh = plot.index_range.high
            self._xmin = plow[0]
            self._ymin = plow[1]

            self._xmax = phigh[0]
            self._ymax = phigh[1]

            # print plot.value_range.low
            # print plot.value_range.high
        else:
            self._xmin, self._xmax = plot.index_range.low, plot.index_range.high
            self._ymin, self._ymax = plot.value_range.low, plot.value_range.high

    def get_axes_group(self):
        editor = TextEditor(enter_set=True, auto_set=False)
        xgrp = VGroup('xtitle', Item('xmin', editor=editor),
                                Item('xmax', editor=editor),
                                # Item('xcolor_', editor = ColorEditor(current_color = 'red'))
                                )
        ygrp = VGroup('ytitle', Item('ymin', editor=editor),
                                Item('ymax', editor=editor),
                                # Item('ycolor_', editor = ColorEditor(current_color = 'blue'))
                                )

        return VGroup(xgrp, ygrp, show_border=True)

    def _get_table_columns(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show')]
        return cols

    def _get_table_editor(self):
        cols = self._get_table_columns()
        table_editor = TableEditor(columns=cols,
                                   selected='_selected',
                                   selection_mode='row')
        return table_editor

    def _get_selected_group(self):
        grp = Group(
                Item('selected',
                     style='custom',
                      show_label=False,
                      editor=InstanceEditor(),
                      enabled_when='selected.show',
                      height=0.25
                     ),
                     show_border=True,
                     springy=False
                             )
        return grp

    def _get_additional_groups(self):
        pass

    def traits_view(self):
        '''
        '''
        vg = VGroup()
        vg.content.append(self.get_axes_group())
        vg.content.append(self._get_selected_group())

        vg.content.append(Item('series_editors',
                             style='custom',
                             editor=self._get_table_editor(),
                             show_label=False,
                             springy=False,
                             height=0.25
                             ))

        agrp = self._get_additional_groups()
        if agrp:
            vg.content.append(agrp)
#        VGroup(
#                        self.get_axes_group(),
#                        self._get_selected_group(),
#
#                        Item('series_editors',
#                             style='custom',
#                             editor=self._get_table_editor(),
#                             show_label=False,
#                             springy=False,
#                             height=0.75
#                             ),
#                        ),
        v = View(vg,
                resizable=True,
                height=0.8,
                width=275,
                title=self.name,
                handler=PlotEditorHandler,
                x=10,
                y=20
                )
        return v

# =============================Property Methods============================
#    def _set_color(self, name, v):
#        if sys.platform == 'win32':
#            v = [vi / 255. for vi in v ]
#
#        self.graph.set_axis_tick_color(name, v, plotid = self.id)
#        self.graph.set_axis_label_color(name, v, plotid = self.id)
#        self.graph.plotcontainer.invalidate_and_redraw()
#
#    def _get_color(self, name):
#        c = Colour()
#        axis = getattr(self.plot, '{}_axis'.format(name))
#        c.SetFromName(axis.tick_color)
#
#        c = 'red'
#        return c
#
#    def _set_xcolor_(self, v):
#        self._set_color('x', v)
#
#    def _set_ycolor_(self, v):
#        self._set_color('y', v)
#
#    def _get_xcolor_(self):
#        self._get_color('x')
#
#    def _get_ycolor_(self):
#        self._get_color('y')

    def _validate_float(self, v, test=None):

        try:
            r = float(v)

            if test is not None:
                r = test(r)

            return r
        except ValueError:
            pass

    def _set_xtitle(self, v):
        self._xtitle = v
        self.graph.set_x_title(v, plotid=self.id)

    def _set_ytitle(self, v):
        self._ytitle = v

        self.graph.set_y_title(v, plotid=self.id)

    def _get_xtitle(self):
        plot = self.graph.plots[self.id]
        return  plot.index_axis.title

    def _get_ytitle(self):
        plot = self.graph.plots[self.id]
        return  plot.value_axis.title

    def _set_xtitle_font(self, v):
        raise NotImplementedError

        plot = self.graph.plots[self.id]

        kv = KivaFontFunc('Arial 24')
        plot.value_axis.title_font = kv.default

    def _set_xmin(self, v):
        self._xmin = v
        self.graph.set_x_limits(min_=v, plotid=self.id)

    def _set_xmax(self, v):
        self._xmax = v
        self.graph.set_x_limits(max_=v, plotid=self.id)

    def _set_ymin(self, v):
        self._ymin = v
        self.graph.set_y_limits(min_=v, plotid=self.id)

    def _set_ymax(self, v):
        self._ymax = v
        self.graph.set_y_limits(max_=v, plotid=self.id)

    def _get_xmin(self):
        return self._xmin

    def _get_xmax(self):
        return self._xmax

    def _get_ymin(self):
        return self._ymin

    def _get_ymax(self):
        return self._ymax

    def _validate_xmin(self, v):
        return self._validate_float(v, test=lambda x: None if x >= self.xmax else x)

    def _validate_xmax(self, v):
        v = self._validate_float(v, test=lambda x: None if x <= self.xmin else x)
        return v

    def _validate_ymin(self, v):
        v = self._validate_float(v, test=lambda x: None if x >= self.ymax else x)
        return v

    def _validate_ymax(self, v):
        v = self._validate_float(v, test=lambda x: None if x <= self.ymin else x)
        return v

# ============= EOF ====================================
