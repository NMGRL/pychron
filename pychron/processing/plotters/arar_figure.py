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
import re

from chaco.array_data_source import ArrayDataSource
from numpy import Inf, inf
from traits.api import HasTraits, Any, Int, Str, Tuple, Property, \
    Event, Bool, cached_property, on_trait_change
from chaco.tools.data_label_tool import DataLabelTool

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.tools.limits_tool import LimitsTool, LimitOverlay
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.processing.plotters.points_label_overlay import PointsLabelOverlay
from pychron.processing.plotters.sparse_ticks import SparseLogTicks, SparseTicks
from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.processing.plotters.flow_label import FlowDataLabel
from chaco.tools.broadcaster import BroadcasterTool
from pychron.graph.tools.rect_selection_tool import RectSelectionOverlay, \
    RectSelectionTool
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.pychron_constants import ARGON_KEYS

PLOT_MAPPING = {'analysis #': 'Analysis Number', 'Analysis #': 'Analysis Number Stacked',
                '%40Ar*': 'Radiogenic 40Ar'}


class BaseArArFigure(HasTraits):
    analyses = Any
    sorted_analyses = Property(depends_on='analyses')
    analysis_group = Property(depends_on='analyses')
    _analysis_group_klass = AnalysisGroup

    group_id = Int
    padding = Tuple((60, 10, 5, 40))
    ytitle = Str
    replot_needed = Event
    _reverse_sorted_analyses = False
    graph = Any

    options = Any

    x_grid_visible = Bool(True)
    y_grid_visible = Bool(True)
    use_sparse_ticks = Bool(True)

    refresh_unknowns_table = Event
    _suppress_table_update = False
    suppress_ylimits_update = False
    suppress_xlimits_update = False
    _omit_key = None
    xpad = None

    title = Str

    def _add_limit_tool(self, plot, orientation):
        t = LimitsTool(component=plot,
                       orientation=orientation)

        o = LimitOverlay(component=plot, tool=t)

        plot.tools.append(t)
        plot.overlays.append(o)

    def build(self, plots):
        """
            make plots
        """
        self._plots = plots

        def _setup_plot(pp, po):

            #add limit tools
            self._add_limit_tool(pp, 'x')
            self._add_limit_tool(pp, 'y')

            pp.value_range.tight_bounds = False
            # print po, po.ylimits, po.has_ylimits()
            # if po.has_ylimits():
            #     print 'setting ylimits {}'.format(po.ylimits)
            #     pp.value_range.set_bounds(*po.ylimits)
            # if po.has_xlimits():
            #     pp.index_range.set_bounds(*po.xlimits)

            pp.x_grid.visible = self.x_grid_visible
            pp.y_grid.visible = self.y_grid_visible

            options = self.options
            pp.x_axis.title_font = options.xtitle_font
            pp.x_axis.tick_label_font = options.xtick_font

            pp.y_axis.title_font = options.ytitle_font
            pp.y_axis.tick_label_font = options.ytick_font

            if po:
                pp.value_scale = po.scale

            if self.use_sparse_ticks:
                if pp.value_scale == 'log':
                    pp.value_axis.tick_generator = SparseLogTicks()
                else:
                    pp.value_axis.tick_generator = SparseTicks()

        graph = self.graph

        vertical_resize = not all([p.height for p in plots])

        graph.vertical_resize = vertical_resize
        graph.clear_has_title()

        title = self.title
        if not title:
            title = self.options.title

        for i, po in enumerate(plots):
            kw = {'padding': self.padding,
                  'ytitle': po.name}

            if po.height:
                kw['bounds'] = [50, po.height]

            if i == (len(plots) - 1):
                kw['title'] = title
            if i == 0:
                kw['ytitle'] = self.ytitle

            p = graph.new_plot(**kw)
            _setup_plot(p, po)

    def plot(self, *args, **kw):
        pass

    def replot(self, *args, **kw):
        pass

    def max_x(self, *args):
        return -Inf

    def min_x(self, *args):
        return Inf

    def mean_x(self, *args):
        return 0

    def _get_omitted(self, ans, omit=None, include_value_filtered=True):
        return [i for i, ai in enumerate(ans)
                if ai.is_omitted(omit, include_value_filtered)]

    def _set_selected(self, ans, sel):
        for i, a in enumerate(ans):
            if not (a.table_filter_omit or a.value_filter_omit or a.is_tag_omitted(self._omit_key)):
                a.temp_status = 1 if i in sel else 0
        self.refresh_unknowns_table = True

    def _filter_metadata_changes(self, obj, func, ans):
        sel = obj.metadata.get('selections', [])
        if sel:
            obj.was_selected = True

            prev = None
            if hasattr(obj, 'prev_selection'):
                prev = obj.prev_selection

            if prev != sel:
                self._set_selected(ans, sel)
                func(sel)

            obj.prev_selection = sel

        elif hasattr(obj, 'was_selected'):
            if obj.was_selected:
                self._set_selected(ans, sel)
                func(sel)
            obj.was_selected = False
            obj.prev_selection = None
        else:
            obj.prev_selection = None

        return sel

    # def _get_mswd(self, ages, errors):
    #     mswd = calculate_mswd(ages, errors)
    #     n = len(ages)
    #     valid_mswd = validate_mswd(mswd, n)
    #     return mswd, valid_mswd, n

    def _cmp_analyses(self, x):
        return x.timestamp

    def _unpack_attr(self, attr):

        if '/' in attr:
            n, d = attr.split('/')

            def gen():
                for ai in self.sorted_analyses:
                    if n in ai.isotopes and d in ai.isotopes:
                        nv, dv = ai.isotopes[n].get_intensity() , ai.isotopes[d].get_intensity()
                        if n is not None and d is not None:
                            yield nv/dv
        else:
            def gen():
                # f = lambda x: x
                # if attr in ARGON_KEYS:
                #     f = lambda x: x.get_intensity()

                for ai in self.sorted_analyses:
                    v= ai.get_value(attr)
                    if v is not None:
                        yield v
                    # yield f(ai.get_value(attr))
        return gen()

    def _set_y_limits(self, a, b, min_=None, max_=None,
                      pid=0, pad=None):

        mi, ma = self.graph.get_y_limits(plotid=pid)

        # print pid, self.group_id, mi, ma, a, b
        mi = min(mi, a)
        ma = max(ma, b)

        if min_ is not None:
            mi = min_
        if max_ is not None:
            ma = max_
        self.graph.set_y_limits(min_=mi, max_=ma, pad=pad, plotid=pid)

    def update_options_limits(self, pid):
        n = len(self.options.aux_plots)
        ap = self.options.aux_plots[n - pid - 1]
        ap.ylimits = self.graph.get_y_limits(pid)
        ap.xlimits = self.graph.get_x_limits(pid)

    #===========================================================================
    # aux plots
    #===========================================================================
    def _get_aux_plot_omits(self, po, ys):
        omits = []
        fs = po.filter_str
        if fs:
            m = re.match(r'[A-Za-z]+', fs)
            if m:
                k = m.group(0)
                ts = [(eval(fs, {k: yi}), i) for i, yi in enumerate(ys)]
                omits = [idx for ti, idx in ts if ti]

        return omits

    def _plot_radiogenic_yield(self, po, plot, pid, **kw):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('rad40_percent')])
        return self._plot_aux('%40Ar*', 'rad40_percent', ys, po, plot, pid, es, **kw)

    def _plot_kcl(self, po, plot, pid, **kw):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('kcl')])
        return self._plot_aux('K/Cl', 'kcl', ys, po, plot, pid, es, **kw)

    def _plot_kca(self, po, plot, pid, **kw):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('kca')])
        return self._plot_aux('K/Ca', 'kca', ys, po, plot, pid, es, **kw)

    def _plot_moles_k39(self, po, plot, pid, **kw):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('k39')])

        return self._plot_aux('K39(fA)', 'k39', ys, po, plot, pid, es, **kw)

    #===============================================================================
    #
    #===============================================================================
    def _add_point_labels(self, scatter):
        labels = []

        f = self.options.analysis_label_format

        if not f:
            f = '{aliquot:02n}{step:}'

        for si in self.sorted_analyses:
            ctx = {'aliquot': si.aliquot,
                   'step': si.step,
                   'sample': si.sample}

            x = f.format(**ctx)
            labels.append(x)

        ov = PointsLabelOverlay(component=scatter,
                                labels=labels,
                                label_box=self.options.label_box
        )
        scatter.underlays.append(ov)

    def _add_error_bars(self, scatter, errors, axis, nsigma,
                        end_caps,
                        visible=True):
        ebo = ErrorBarOverlay(component=scatter,
                              orientation=axis,
                              nsigma=nsigma,
                              visible=visible,
                              use_end_caps=end_caps)

        scatter.underlays.append(ebo)
        setattr(scatter, '{}error'.format(axis), ArrayDataSource(errors))
        return ebo

    def _add_scatter_inspector(self,
                               # container,
                               scatter,
                               add_tool=True,
                               value_format=None,
                               additional_info=None):
        if add_tool:
            broadcaster = BroadcasterTool()
            scatter.tools.append(broadcaster)

            rect_tool = RectSelectionTool(scatter)
            rect_overlay = RectSelectionOverlay(component=scatter,
                                                tool=rect_tool)

            scatter.overlays.append(rect_overlay)
            broadcaster.tools.append(rect_tool)

            if value_format is None:
                value_format = lambda x: '{:0.5f}'.format(x)
            point_inspector = AnalysisPointInspector(scatter,
                                                     analyses=self.sorted_analyses,
                                                     convert_index=lambda x: '{:0.3f}'.format(x),
                                                     value_format=value_format,
                                                     additional_info=additional_info)

            pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                       tool=point_inspector)

            scatter.overlays.append(pinspector_overlay)
            broadcaster.tools.append(point_inspector)

            # u = lambda a, b, c, d: self.update_graph_metadata(a, b, c, d)
            scatter.index.on_trait_change(self.update_graph_metadata, 'metadata_changed')
            #===============================================================================
            # labels
            #===============================================================================


    def _add_data_label(self, s, text, point, bgcolor='transparent',
                        label_position='top right', color=None, append=True, **kw):
        if color is None:
            color = s.color

        label = FlowDataLabel(component=s, data_point=point,
                              label_position=label_position,
                              label_text=text,
                              border_visible=False,
                              bgcolor=bgcolor,
                              show_label_coords=False,
                              marker_visible=False,
                              text_color=color,

                              # setting the arrow to visible causes an error when reading with illustrator
                              # if the arrow is not drawn
                              arrow_visible=False,
                              **kw)
        s.overlays.append(label)
        tool = DataLabelTool(label)
        if append:
            label.tools.append(tool)
        else:
            label.tools.insert(0, tool)

        label.on_trait_change(self._handle_overlay_move, 'label_position')
        return label

    def _build_label_text(self, x, we, mswd, valid_mswd, n,
                          percent_error=False,
                          value_sig_figs=3,
                          error_sig_figs=4
    ):
        display_n = True
        display_mswd = n >= 2
        if display_n:
            n = 'n= {}'.format(n)
        else:
            n = ''

        if display_mswd:
            vd = '' if valid_mswd else '*'
            mswd = '{}mswd= {:0.2f}'.format(vd, mswd)
        else:
            mswd = ''

        sx = floatfmt(x, value_sig_figs)
        swe = floatfmt(we, error_sig_figs)

        if self.options.index_attr in ('uF', 'Ar40/Ar36'):
            me = '{} +/-{}'.format(sx, swe)
        else:
            age_units = self._get_age_units()
            pe = ''
            if percent_error:
                pe = '({})'.format(format_percent_error(x, we, include_percent_sign=True))

            me = '{} +/-{}{} {}'.format(sx, swe, pe, age_units)

        return u'{} {} {}'.format(me, mswd, n)

    def _get_age_units(self):
        a = 'Ma'
        if self.analyses:
            a = self.analyses[0].arar_constants.age_units
        return a

    def _set_renderer_selection(self, rs, sel):
        for rend in rs:
            meta = {'selections': sel}
            rend.index.trait_set(metadata=meta,
                                 trait_change_notify=False)

    def _handle_label_move(self, obj, name, old, new):
        axps = [a for a in self.options.aux_plots if a.use][::-1]
        for i, p in enumerate(self.graph.plots):
            if next((pp for pp in p.plots.itervalues()
                     if obj.component == pp[0]), None):
                axp = axps[i]
                if hasattr(new, '__iter__'):
                    new = map(float, new)
                else:
                    new = float(new)
                axp.set_overlay_position(obj.id, new)


    def _handle_overlay_move(self, obj, name, old, new):
        axps = [a for a in self.options.aux_plots if a.use][::-1]
        for i, p in enumerate(self.graph.plots):
            if next((pp for pp in p.plots.itervalues()
                     if obj.component == pp[0]), None):
                axp = axps[i]
                if hasattr(new, '__iter__'):
                    new = map(float, new)
                else:
                    new = float(new)
                axp.set_overlay_position(obj.id, new)

                break

    @on_trait_change('graph:plots:index_mapper:updated')
    def _handle_index_range(self, obj, name, old, new):

        if not isinstance(new, bool):
            if new.low == -inf or new.high == inf:
                return

            if self.suppress_xlimits_update:
                return

            for p in self.graph.plots:
                if p.index_mapper == obj:
                    op = self.options.aux_plots[-1]
                    op.xlimits = (new.low, new.high)
                    # print 'setting xlimits', op.xlimits, op, op.name
                    break

    @on_trait_change('graph:plots:value_mapper:updated')
    def _handle_value_range(self, obj, name, old, new):
        if not isinstance(new, bool):
            if self.suppress_ylimits_update:
                return

            for p in self.graph.plots:
                if p.value_mapper == obj:
                    plot = p
                    title = plot.y_axis.title

                    if title in PLOT_MAPPING:
                        title = PLOT_MAPPING[title]

                    for op in self.options.aux_plots:
                        if title.startswith(op.name):
                            op.ylimits = (new.low, new.high)
                            break
                    break

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_sorted_analyses(self):
        return sorted(self.analyses,
                      key=self._cmp_analyses,
                      reverse=self._reverse_sorted_analyses)

    @cached_property
    def _get_analysis_group(self):
        return self._analysis_group_klass(analyses=self.sorted_analyses)
        #============= EOF =============================================
