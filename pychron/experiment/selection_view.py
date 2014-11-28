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

#============= enthought library imports =======================
from traits.api import Instance, List, Bool
from traitsui.api import View, Item, VGroup, HGroup, HSplit, InstanceEditor, spring
from chaco.tools.zoom_tool import ZoomTool
from chaco.tools.scatter_inspector import ScatterInspector
from chaco.abstract_overlay import AbstractOverlay
from chaco.data_label import DataLabel
from kiva.fonttools import Font
#============= standard library imports ========================
import numpy as np

#============= local library imports  ==========================
from pychron.viewable import Viewable
from pychron.database.selectors.isotope_selector import IsotopeAnalysisSelector
from pychron.graph.stacked_graph import StackedGraph


class LegendOverlay(AbstractOverlay):
    def overlay(self, component, gc, *args, **kw):

        gc.save_state()
        gc.set_font(Font('Monaco'))
        x = component.x
        y2 = component.y2

        gc.set_fill_color((1, 1, 1))
        w = 100
        h = 110

        gc.rect(x + 5, y2 - 5 - h, w, h)
        gc.draw_path()

        machines = ['jan', 'obama', 'map']
        colors = [(1, 0.5, 0), (0, 0, 1), (1, 0, 0)]
        xo = x + 5
        yo = y2 - 10
        texth = 12
        for i, (mi, color) in enumerate(zip(machines, colors)):
            gc.set_fill_color(color)
            yi = yo - (texth) * (i + 1)
            gc.set_text_position(xo + 20, yi)
            gc.show_text(mi)

#        markers = ['circle', 'square', 'diamond', 'triangle']
        ats = ['blank', 'air', 'cocktail', 'unknown', 'background']
        gc.set_fill_color((0, 0, 0))
        for i, si in enumerate(ats):
            yy = yi - (texth) * (i + 1)
            try:
                plot = component.plots['jan {}'.format(si)][0]
            except KeyError:
                continue
            pcolor, plot.color = plot.color, 'black'
            mpcolor, plot.outline_color = plot.outline_color, 'black'
            plot._render_icon(gc, xo + 5, yy, 5, 5)
            plot.color = pcolor
            plot.outline_color = mpcolor
            gc.set_text_position(xo + 20, yy)
            gc.show_text(si)

        gc.restore_state()

class SelectionView(Viewable):
    table = Instance(IsotopeAnalysisSelector)
    graph = Instance(StackedGraph)
    data_labels_visible = Bool(True)
    data_labels = List
    def _data_labels_visible_changed(self):
        for di in self.data_labels:
            di.visible = self.data_labels_visible
        self.graph.redraw()

    def _graph_default(self):
        g = StackedGraph(container_dict=dict(padding=5))
        plot = g.new_plot(
#                   show_legend='ul',
                   padding=5)


        plot.overlays.append(ZoomTool(plot,
                                      minimum_screen_delta=5,
                                      enable_wheel=False,
                                      drag_button='left',
                                      tool_mode='range',
                                      always_on_top=True,
                                      axis='index'
                                      ))

#        plot.on_trait_change(self._update, 'index_mapper.range.updated')
        plot.overlays.append(LegendOverlay(plot))
        g.set_axis_traits(axis='y', visible=False)
        g.set_axis_traits(axis='x', visible=False)
        g.set_grid_traits(grid='x', visible=False)
        g.set_grid_traits(grid='y', visible=False)
        return g

    def build_graph(self):

        skw = dict(type='scatter', marker_size=3)
#            skw = dict(type='bar')
        g = self.graph
        xs = []
        ys = []
        ats = ['blank', 'air', 'cocktail', 'unknown', 'background']
#        ats += ['blank_air', 'blank_cocktail', 'blank_unknown']
        machines = ['jan', 'obama', 'map']
        rids = []
        def test(ri, at, mach):
            if at == 'blank':
                attest = ri.analysis_type.startswith('blank')
            else:
                attest = ri.analysis_type == at

            if attest:
                return ri.mass_spectrometer == mach

        for mach in machines:
            for i, at in enumerate(ats):
                dd = [(ri.shortname, ri.timestamp)
                               for ri in self.table.records
                                    if test(ri, at, mach)

                        ]
                if dd:
                    ni, xi = zip(*dd)
                else:
                    xi = []
                    ni = []
                xi = np.array(xi)
                n = len(xi)
                xs.append(xi)
                ys.append(np.array(range(n)) + 1 + 3 * i)
                rids.append(ni)

        mm = [min(xj) for xj in xs if len(xj)]
        if not mm:
            return
        xmi = min(mm)
        mm = [max(yj) for yj in ys if len(yj)]
        yma = max(mm)

        xs = np.array([xk - xmi for xk in xs])
        ys = np.array(ys)
        mm = [max(xj) for xj in xs if len(xj)]
        xma = max(mm)

        colors = ['orange', 'blue', 'green']
        markers = ['circle', 'square', 'diamond', 'triangle', 'cross']

        def ffunc(s):
            def func(new):
                if new:
                    self._update_graph(s, xmi)
            return func

        def fffunc(s):
            def func(new):
                if new:
                    self._update(s, xmi)
            return func

        for i, (name, color) in enumerate(zip(machines, colors)):
            xxj = xs[i * 5:i * 5 + 5]
            yyj = ys[i * 5:i * 5 + 5]
            nnj = rids[i * 5:i * 5 + 5]
            for at, xx, yy, nn, marker in zip(ats, xxj, yyj, nnj, markers):
                s, _ = g.new_series(xx, yy, marker=marker, color=color, **skw)
                g.set_series_label('{} {}'.format(name, at))
#                self.add_trait('scatter_{}_{}'.format(at, name), s)

                tool = ScatterInspector(s, selection_mode='single')
                s.tools.append(tool)

                s.index.on_trait_change(ffunc(s), 'metadata_changed')

                for xi, yi, ni in zip(xx, yy, nn):
                    dl = DataLabel(component=s,
                                   font=Font('Monaco'),
                                   data_point=(xi, yi),
                                   label_position='top left',
                                   bgcolor='white',
#                                   label_format='%s',
                                   label_text=ni,
                                   show_label_coords=False,
                                   arrow_visible=False,
                                   marker_visible=False
                                   )
                    s.overlays.append(dl)
                    self.data_labels.append(dl)
                # add range selection tool
#                s.active_tool = RangeSelection(s, left_button_selects=True)
#                s.overlays.append(RangeSelectionOverlay(component=s))
#                s.index.on_trait_change(getattr(self, '_update_{}'.format(at)), 'metadata_changed')

        g.set_x_limits(min_=0, max_=xma, pad='0.1')
        g.set_y_limits(min_=0, max_=yma * 1.1)

#    def _update(self, sc, nds):
#        #rescale y limits
#        plot = self.graph.plots[0]
#        if self.data_labels:
#            low = plot.index_mapper.range.low
#            high = plot.index_mapper.range.high
#            #get points in the range
#            xs, ys = zip(*[di.data_point for di in self.data_labels])
#            xs = np.array(xs)
#            ys = np.array(ys)
#
#            tags = np.invert(np.bitwise_or(xs < low, xs > high))
#            nys = ys[tags]
#    #        dls = [di for di in self.data_labels if low <= di.data_point[0] <= high]
#            if nys.shape[0]:
#                nlow = min(nys)
#                nhigh = max(nys)
#
# #                nhigh = np.random.randint(100000)
#                print 'looo', nlow, nhigh
#                sc.value_mapper.range.low = nlow
#                sc.value_mapper.range.high = nhigh
#    #            print plot.value_mapper.range.low_setting
#    #            print plot.value_mapper.range.high_setting
# #                self.graph.set_y_limits(nlow, nhigh, pad='0.1')
# #                plot.value_mapper.range.low = nlow
# #                plot.value_mapper.range.high = nhigh
#                self.graph.redraw()


    def _update_graph(self, scatter, xmi):
#        sel = scatter.index.metadata.get('selections')
        hover = scatter.index.metadata.get('hover')
        if hover:
            xs = scatter.index.get_data()

            ts = xs[hover] + xmi
            result = next((ri for ri in self.table.records
                           if abs(ri.timestamp - ts) < 1), None)

            self.table.selected = [result]

    def traits_view(self):
        tgrp = Item('table', show_label=False,
                    style='custom', width=0.3,
                    editor=InstanceEditor(view='panel_view')
                    )
        ggrp = VGroup(
                     HGroup(Item('data_labels_visible', label='Label'), spring),
                     Item('graph', show_label=False, style='custom', width=0.7)
                     )
        v = View(HSplit(tgrp,
                        ggrp),
                 width=1000,
                 height=500,
                 title='Recent Analyses',
                 resizable=True)
        return v
# ============= EOF =============================================
