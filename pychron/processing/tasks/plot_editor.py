#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
import copy
from chaco.axis import DEFAULT_TICK_FORMATTER
from chaco.base_xy_plot import BaseXYPlot
from chaco.scatterplot import ScatterPlot
from enable.colors import transparent_color
from enable.enable_traits import LineStyle
from enable.markers import MarkerTrait
from traits.api import HasTraits, Any, Float, Int, on_trait_change, Bool, \
    Instance, List, Range, Color, Str, Font, Enum
from traitsui.api import View, Item, Group, VGroup, UItem, Heading, HGroup, EnumEditor
# from pyface.timer.do_later import do_later
# from traitsui.editors.range_editor import RangeEditor
# from numpy.core.numeric import Inf
# from pychron.ui.double_spinner import DoubleSpinnerEditor
#============= standard library imports ========================
#============= local library imports  ==========================
class EFloat(Float):
    enter_set = True
    auto_set = False


class EInt(Int):
    enter_set = True
    auto_set = False


class Grid(HasTraits):
    plot_grid = Any
    show_grid = Bool
    line_style = LineStyle
    line_width = Int

    def _plot_grid_changed(self):
        g = self.plot_grid
        if g:
            traits = {'show_grid': g.visible,
                      'line_style': g.line_style,
                      'line_width': g.line_width}

            self.trait_set(trait_change_notify=False, **traits)

    @on_trait_change('show_grid, line_+')
    def _update_grids(self, name, new):
        if name == 'show_grid':
            name = 'visible'

        setattr(self.plot_grid, name, new)
        self.plot_grid.invalidate_and_redraw()

    def traits_view(self):
        v = View(HGroup(Item('show_grid', label='Show Grid'),
                        UItem('line_style'),
                        UItem('line_width')))
        return v


class Axis(HasTraits):
    plot_axis = Any

    title_spacing = EFloat
    title_spacing_auto = Bool
    tick_visible = Bool
    title_font_size = Enum(6, 8, 10, 11, 12, 14, 15, 18, 22, 24, 36)
    tick_font_size = Enum(6, 8, 10, 11, 12, 14, 15, 18, 22, 24, 36)
    tick_interval = Float
    tick_interval_auto = Bool

    grid = Instance(Grid, ())

    def _plot_axis_changed(self):
        vaxis = self.plot_axis
        if vaxis:
            traits = {}
            ts = vaxis.title_spacing
            if ts == 'auto':
                traits['title_spacing_auto'] = True
            else:
                traits['title_spacing_auto'] = False
                traits['title_spacing'] = ts

            traits['title_font_size'] = vaxis.title_font.size
            traits['tick_visible'] = vaxis.tick_visible

            ti = vaxis.tick_interval
            if ti == 'auto':
                traits['tick_interval_auto'] = True
            else:
                traits['tick_interval_auto'] = False
                traits['tick_interval'] = ti

            traits['tick_font_size'] = vaxis.tick_label_font.size
            self.trait_set(trait_change_notify=False, **traits)

    @on_trait_change('title_font_size')
    def _update_title_font(self):
        f = copy.copy(self.plot_axis.title_font)

        f.size = self.title_font_size
        self.plot_axis.title_font = f
        self.plot_axis.invalidate_and_redraw()

    @on_trait_change('tick_font_size')
    def _update_tick_font(self):
        f = copy.copy(self.plot_axis.tick_label_font)

        f.size = self.tick_font_size
        self.plot_axis.tick_label_font = f
        self.plot_axis.invalidate_and_redraw()

    @on_trait_change('title_spacing')
    def _update_value_axis(self, name, new):
        if self.plot_axis:
            self.plot_axis.title_spacing = new
            self.plot_axis.invalidate_and_redraw()

    @on_trait_change('tick_visible')
    def _update_tick_visible(self, name, new):
        if new:
            fmt = DEFAULT_TICK_FORMATTER
        else:
            fmt = lambda x: ''
        self.plot_axis.tick_visible = new
        self.plot_axis.trait_set(**{'tick_visible': new,
                                    'tick_label_formatter': fmt})
        self.plot_axis.invalidate_and_redraw()

    @on_trait_change('tick_interval_auto, title_spacing_auto')
    def _tick_interval_auto_changed(self, name, new):
        name = name.replace('_auto', '')
        if new:
            ti = 'auto'
        else:
            ti = getattr(self, name)

        self.plot_axis.trait_set(**{name: ti})
        self.plot_axis.invalidate_and_redraw()

    @on_trait_change('tick_interval, title_spacing')
    def _tick_interval_changed(self, name, new):
        self.plot_axis.trait_set(**{name: new})
        self.plot_axis.invalidate_and_redraw()

    def traits_view(self):
        y_grp = Group(
            HGroup(Item('title_spacing_auto', label='Auto'),
                   Item('title_spacing', enabled_when='not title_spacing_auto')),
            Item('tick_visible'),
            Item('title_font_size'),
            Item('tick_font_size'),
            HGroup(Item('tick_interval_auto', label='Auto'),
                   Item('tick_interval', enabled_when='not tick_interval_auto')),
            UItem('grid', style='custom')
        )
        v = View(y_grp)
        return v


class PlotEditor(HasTraits):
    plot = Any
    analyses = Any

    xmin = EFloat
    xmax = EFloat
    ymin = EFloat
    ymax = EFloat

    xauto = Bool
    yauto = Bool

    auto_xpad = Float(0.1)

    padding_left = EInt
    padding_right = EInt
    padding_top = EInt
    padding_bottom = EInt

    x_axis = Instance(Axis, ())
    y_axis = Instance(Axis, ())

    #renderers = List
    selected_renderer_name = Str
    selected_renderer = Instance('RendererEditor')
    renderer_names = List


    def _selected_renderer_name_changed(self):
        self.selected_renderer = self._get_selected_renderer()

    def _get_selected_renderer(self):
        for k, ps in self.plot.plots.iteritems():
            r = ps[0]
            if k == self.selected_renderer_name:
                if isinstance(r, ScatterPlot):
                    klass = ScatterRendererEditor
                else:
                    klass = LineRendererEditor

                rend = klass(name=k,
                             renderer=r)
                return rend

    def _plot_changed(self):

        traits = {'xmin': self.plot.index_range.low,
                  'xmax': self.plot.index_range.high,
                  'ymin': self.plot.value_range.low,
                  'ymax': self.plot.value_range.high}

        for attr in ('left', 'right', 'top', 'bottom'):
            attr = 'padding_{}'.format(attr)
            v = getattr(self.plot, attr)
            traits[attr] = v

        vaxis = self.plot.value_axis
        self.y_axis.plot_axis = vaxis
        self.y_axis.grid.plot_grid = self.plot.y_grid

        vaxis = self.plot.index_axis
        self.x_axis.plot_axis = vaxis
        self.x_axis.grid.plot_grid = self.plot.x_grid

        self.trait_set(trait_change_notify=False, **traits)

        rs = []
        for k, ps in self.plot.plots.iteritems():
            r = ps[0]
            editable = True
            if hasattr(r, 'editable'):
                editable = r.editable

            if editable:
                rs.append(k)
                #if isinstance(r, ScatterPlot):
                #    klass = ScatterRendererEditor
                #else:
                #    klass = LineRendererEditor
                #
                #rs.append(klass(name=k,
                #                renderer=r))

        #self.renderers = rs
        def pred(x):
            if '-' in x:
                try:
                    return int(x.split('-')[1])
                except ValueError:
                    return x
            else:
                return x

        rs = sorted(rs, key=pred)
        self.renderer_names = rs
        if rs:
            self.selected_renderer_name = rs[0]

    @on_trait_change('padding+')
    def _update_padding(self, name, new):
        self.plot.trait_set(**{name: new})
        self.plot._layout_needed = True
        self.plot.invalidate_and_redraw()

    def _xmin_changed(self):
        print 'xmin change'
        p = self.plot
        v = p.index_range.high
        if self.xmin < v:
            p.index_range.low_setting = self.xmin
            self.xauto = False

        try:
            p.default_index.metadata_changed = True
        except AttributeError:
            pass

    def _xmax_changed(self):
        print 'xmax change'
        p = self.plot
        v = p.index_range.low
        if self.xmax > v:
            p.index_range.high_setting = self.xmax
            self.xauto = False

        try:
            p.default_index.metadata_changed = True
        except AttributeError:
            pass

    def _ymin_changed(self):
        p = self.plot
        v = p.value_range.high
        if self.ymin < v:
            p.value_range.low_setting = self.ymin
            self.yauto = False

    def _ymax_changed(self):
        p = self.plot
        v = p.value_range.low
        if self.ymax > v:
            p.value_range.high_setting = self.ymax
            self.yauto = False

    def _xauto_changed(self):
        if self.xauto:
            #p = self.plot
            dd = [a.uage for a in self.analyses]

            mid = [di.nominal_value - di.std_dev for di in dd]
            mad = [di.nominal_value + di.std_dev for di in dd]
            #mid=[di.nominal_value for di in dd]
            #mad=[di.nominal_value for di in dd]
            mi, ma = min(mid), max(mad)

            p = self.auto_xpad * (ma - mi)
            self.xmin = mi - p
            self.xmax = ma + p

    def traits_view(self):
        #renderers_grp = Group(
        #    UItem('renderers', editor=ListEditor(mutable=False,
        #                                         style='custom',
        #                                         editor=InstanceEditor())),
        #    label='Plots')
        renderers_grp = Group(
            VGroup(UItem('selected_renderer_name',
                         editor=EnumEditor(name='renderer_names')),
                   UItem('selected_renderer', style='custom')),
            label='Selected Plot')

        xlim_grp = HGroup(Item('xauto', label='Auto'),
                          UItem('xmin', format_str='%0.4f',
                                enabled_when='not xauto'),
                          UItem('xmax', format_str='%0.4f',
                                enabled_when='not xauto'),
                          label='X Limits')
        ylim_grp = HGroup(UItem('ymin', format_str='%0.4f'),
                          UItem('ymax', format_str='%0.4f'),
                          label='Y Limits')
        xgrp=VGroup(xlim_grp,
                    UItem('x_axis', style='custom'), label='X Axis')
        ygrp=VGroup(ylim_grp,
                   UItem('y_axis', style='custom'), label='Y Axis')

        layout_grp = VGroup(
            Item('padding_left', label='Left'),
            Item('padding_right', label='Right'),
            Item('padding_top', label='Top'),
            Item('padding_bottom', label='Bottom'),
            label='Padding')

        general_grp = Group(
            xgrp,ygrp,
            layout_grp,
            renderers_grp, layout='tabbed')

        v = View(general_grp)

        return v


class RendererEditor(HasTraits):
    renderer = Instance(BaseXYPlot)
    visible = Bool
    color = Color

    @on_trait_change('visible, color')
    def _update_value(self, name, new):
        #print 'render editor',name,new
        self._set_value(name, new)

    def _set_value(self, name, new):
        self.renderer.trait_set(**{name: new})
        self.renderer.request_redraw()

    def _renderer_changed(self):
        self.line_width = self.renderer.line_width
        self.visible = self.renderer.visible
        #self.color = self.renderer.color
        self._sync()

    def _sync(self):
        pass

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(Heading(self.name),
                       UItem('visible')),
                self._get_group()
            )
        )
        return v


class LineRendererEditor(RendererEditor):
    line_width = Range(0.0, 10.0)
    line_style = LineStyle

    @on_trait_change('line+')
    def _update_values2(self, name, new):
        self._set_value(name, new)

    def _get_group(self):
        g = VGroup(
            Item('color'),
            Item('line_width', label='Width'),
            Item('line_style', label='Style'),
            enabled_when='visible'
        )
        return g


class ScatterRendererEditor(RendererEditor):
    marker_size = Range(0.0, 10.0)
    outline_color = Color
    marker = MarkerTrait
    selection_marker_size = Range(0.0, 10.0)

    @on_trait_change('marker+, outline_color')
    def _update_values2(self, name, new):
        self._set_value(name, new)
        #if name.startswith('marker'):
        #    self._set_value('selection_{}'.format(name), new)

    def _sync(self):
        self.outline_color = self.renderer.outline_color
        self.marker = self.renderer.marker
        self.marker_size = self.renderer.marker_size

        self.selection_marker_size = self.renderer.selection_marker_size

    def _get_group(self):
        g = VGroup(
            Item('color'),
            Item('outline_color', label='Outline'),
            Item('marker'),
            Item('marker_size', label='Size'),
            enabled_when='visible'
        )
        return g


class AnnotationEditor(HasTraits):
    component = Any

    border_visible = Bool(True)
    border_width = Range(0, 10)
    border_color = Color

    font = Font('modern 12')
    text_color = Color
    bgcolor = Color
    text = Str
    bg_visible = Bool(True)

    @on_trait_change('component:text')
    def _component_text_changed(self):
        self.text = self.component.text

    def _component_changed(self):
        if self.component:
            traits = ('border_visible',
                      'border_width',
                      'text')

            d = self.component.trait_get(traits)
            self.trait_set(self, **d)
            for c in ('border_color', 'text_color', 'bgcolor'):
                v = getattr(self.component, c)
                if not isinstance(v, str):
                    v = v[0] * 255, v[1] * 255, v[2] * 255

                self.trait_set(**{c: v})

    def _bg_visible_changed(self):
        if self.component:
            if self.bg_visible:
                self.component.bgcolor = self.bgcolor
            else:
                self.component.bgcolor = transparent_color
            self.component.request_redraw()

    @on_trait_change('border_+, text_color, bgcolor, text')
    def _update(self, name, new):
        if self.component:
            self.component.trait_set(**{name: new})
            self.component.request_redraw()

    @on_trait_change('font')
    def _update_font(self):
        if self.component:
            self.component.font = str(self.font)
            self.component.request_redraw()

    def traits_view(self):
        v = View(
            VGroup(
                Item('font',
                     width=75, ),
                Item('text_color', label='Text'),
                HGroup(
                    UItem('bg_visible',
                          tooltip='Is the background transparent'
                    ),
                    Item('bgcolor', label='Background',
                         enabled_when='bg_visible'
                    ),
                ),
                UItem('text', style='custom'),
                Group(
                    Item('border_visible'),
                    Item('border_width', enabled_when='border_visible'),
                    Item('border_color', enabled_when='border_visible'),
                    label='Border'

                ),
                visible_when='component'
            )
        )
        return v

        #============= EOF =============================================
