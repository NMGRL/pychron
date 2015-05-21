# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================

from chaco.array_data_source import ArrayDataSource
from traits.api import HasTraits, Any, Int, Str, Property, \
    Event, Bool, cached_property, List, Float
from chaco.tools.data_label_tool import DataLabelTool
from chaco.tools.broadcaster import BroadcasterTool
# ============= standard library imports ========================
from numpy import Inf
import re
from uncertainties import std_dev, nominal_value, ufloat
# ============= local library imports  ==========================
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.ml_label import MPlotAxis
from pychron.graph.tools.axis_tool import AxisTool
from pychron.graph.tools.limits_tool import LimitsTool, LimitOverlay
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.processing.plot.overlays.points_label_overlay import PointsLabelOverlay
from pychron.processing.plot.sparse_ticks import SparseLogTicks, SparseTicks
from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.processing.plot.flow_label import FlowDataLabel
from pychron.graph.tools.rect_selection_tool import RectSelectionOverlay, \
    RectSelectionTool
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.pychron_constants import PLUSMINUS

PLOT_MAPPING = {'analysis #': 'Analysis Number', 'Analysis #': 'Analysis Number Stacked',
                '%40Ar*': 'Radiogenic 40Ar'}


class BaseArArFigure(HasTraits):
    analyses = Any
    sorted_analyses = Property(depends_on='analyses')
    analysis_group = Property(depends_on='analyses')
    _analysis_group_klass = AnalysisGroup

    group_id = Int
    # padding = Tuple((60, 10, 5, 40))
    ytitle = Str
    replot_needed = Event
    _reverse_sorted_analyses = False
    graph = Any

    options = Any

    # x_grid_visible = Bool(True)
    # y_grid_visible = Bool(True)
    use_sparse_ticks = Bool(True)

    refresh_unknowns_table = Event
    _suppress_table_update = False
    suppress_ylimits_update = False
    suppress_xlimits_update = False
    _omit_key = None
    xpad = None

    title = Str

    bgcolor = None

    ymas = List
    ymis = List
    xmi = Float
    xma = Float
    xtitle = None

    _has_formatting_hash = None

    def build(self, plots):
        """
            make plots
        """
        self._plots = plots
        graph = self.graph

        vertical_resize = not all([p.height for p in plots])

        graph.vertical_resize = vertical_resize
        graph.clear_has_title()

        title = self.title
        if not title:
            title = self.options.title

        for i, po in enumerate(plots):
            # kw = {'padding': self.padding,
            # 'ytitle': po.name}
            kw = {'ytitle': po.name}
            if po.height:
                kw['bounds'] = [50, po.height]

            if i == (len(plots) - 1):
                kw['title'] = title

            if i == 0 and self.ytitle:
                kw['ytitle'] = self.ytitle

            if not po.ytitle_visible:
                kw['ytitle'] = ''

            if self.xtitle:
                kw['xtitle'] = self.xtitle
            p = graph.new_plot(**kw)
            # set a tag for easy identification
            p.y_axis.tag = po.name
            self._setup_plot(i, p, po)

            # if self.options.use_legend:
            # if True:
            # self._add_legend()

    def post_make(self):
        pass

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

    # private
    def _setup_plot(self, i, pp, po):
        # add limit tools
        self._add_limit_tool(pp, 'x')
        self._add_limit_tool(pp, 'y')

        self._add_axis_tool(pp, pp.x_axis)
        self._add_axis_tool(pp, pp.y_axis)

        pp.value_range.on_trait_change(lambda: self.update_options_limits(i), 'updated')
        pp.index_range.on_trait_change(lambda: self.update_options_limits(i), 'updated')
        pp.value_range.tight_bounds = False

        options = self.options
        pp.x_grid.visible = options.use_xgrid
        pp.y_grid.visible = options.use_ygrid
        # pp.x_grid.visible = self.x_grid_visible
        # pp.y_grid.visible = self.y_grid_visible

        self._set_formatting(pp)

        # pp.bgcolor = options.plot_bgcolor
        for attr in ('left', 'right', 'top'):
            setattr(pp, 'padding_{}'.format(attr),
                    getattr(options, 'padding_{}'.format(attr)))

        if not i:
            pp.padding_bottom = options.padding_bottom

        if po:
            pp.value_scale = po.scale
            if not po.ytick_visible:
                pp.y_axis.tick_visible = False
                pp.y_axis.tick_label_formatter = lambda x: ''

        if self.use_sparse_ticks:
            if pp.value_scale == 'log':
                pp.value_axis.tick_generator = SparseLogTicks()
            else:
                pp.value_axis.tick_generator = SparseTicks()

    def _set_formatting(self, pp):

        # implement a formatting_options object.
        # this object defines the fonts, sizes and some colors.
        # there will be 5 default formatting_object objects
        # the user may save more. a single formatting object maybe applied to any of the options types
        # e.g ideogram, spectrum, etc. therefore the formatting_options object should be defined
        # at the PlotterOptionsManager level and not PlotterOptions.
        # defaults
        # 1. screen
        # 2. pdf
        # 3. poster
        # 4. projector
        # 5. publication
        #
        # in the future publication may be divided into various formats. e.g. 1/2 column, 2/3 column etc.
        # a Null formatting option should be available. If null is used the the fonts etc are defined by
        # the options object.

        options = self.options

        # self.formatting_options = None
        # from pychron.paths import paths
        # self.formatting_options = FormattingOptions(paths.presentation_formatting_options)

        if options.formatting_options is None:
            self._set_options_format(pp)
        else:

            if self.options.has_changes():
                self._set_options_format(pp)
            else:
                # print 'using formatting options'
                fmt_opt = options.formatting_options
                for name, axis in (('x', pp.x_axis), ('y', pp.y_axis)):
                    for attr in ('title_font', 'tick_label_font', 'tick_in', 'tick_out'):
                        value = fmt_opt.get_value(name, attr)
                        setattr(axis, attr, value)

                pp.bgcolor = fmt_opt.plot_bgcolor

            options.set_hash()

    def _set_options_format(self, pp):
        # print 'using options format'

        options = self.options
        pp.x_axis.title_font = options.xtitle_font
        pp.x_axis.tick_label_font = options.xtick_font
        pp.x_axis.tick_in = options.xtick_in
        pp.x_axis.tick_out = options.xtick_out

        pp.y_axis.title_font = options.ytitle_font
        pp.y_axis.tick_label_font = options.ytick_font
        pp.y_axis.tick_in = options.ytick_in
        pp.y_axis.tick_out = options.ytick_out

        pp.bgcolor = options.plot_bgcolor

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
    # mswd = calculate_mswd(ages, errors)
    # n = len(ages)
    # valid_mswd = validate_mswd(mswd, n)
    #     return mswd, valid_mswd, n

    def _cmp_analyses(self, x):
        return x.timestamp

    def _unpack_attr(self, attr):

        # if '/' in attr:
        #     def gen():
        #         for ai in self.sorted_analyses:
        #             r = ai.get_ratio(attr)
        #             yield r or ufloat(0,0)
        #             # nv, dv = ai.isotopes[n].get_intensity() , ai.isotopes[d].get_intensity()
        #             # if n is not None and d is not None:
        #             #     yield nv/dv
        # else:
        def gen():
            # f = lambda x: x
            # if attr in ARGON_KEYS:
            #     f = lambda x: x.get_intensity()

            for ai in self.sorted_analyses:
                v = ai.get_value(attr)
                yield v or ufloat(0, 0)
                # if v is not None:
                #     yield v
                # yield f(ai.get_value(attr))

        return gen()

    def _set_y_limits(self, a, b, min_=None, max_=None,
                      pid=0, pad=None):

        mi, ma = self.graph.get_y_limits(plotid=pid)

        # print pid, self.group_id, mi, ma, a, b
        # mi = min(mi, a)
        # ma = max(ma, b)

        mi = min_ if min_ is not None else min(mi, a)

        ma = max_ if max_ is not None else max(ma, b)

        self.graph.set_y_limits(min_=mi, max_=ma, pad=pad, plotid=pid, pad_style='upper')

    def update_options_limits(self, pid):
        n = len(self.options.aux_plots)
        ap = self.options.aux_plots[n - pid - 1]
        if not self.suppress_ylimits_update:
            ap.ylimits = self.graph.get_y_limits(pid)

        if not self.suppress_xlimits_update:
            ap.xlimits = self.graph.get_x_limits(pid)

    # ===========================================================================
    # aux plots
    # ===========================================================================
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

    def _plot_raw_40_36(self, po, plot, pid, **kw):
        k = 'uAr40/Ar36'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('noncor. <sup>40</sup>Ar/<sup>36</sup>Ar', k, ys, po, plot, pid, es, **kw)

    def _plot_ic_40_36(self, po, plot, pid, **kw):
        k = 'Ar40/Ar36'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('<sup>40</sup>Ar/<sup>36</sup>Ar', k, ys, po, plot, pid, es, **kw)

    def _plot_icf_40_36(self, po, plot, pid, **kw):
        k = 'icf_40_36'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('ifc <sup>40</sup>Ar/<sup>36</sup>Ar', k, ys, po, plot, pid, es, **kw)

    def _plot_radiogenic_yield(self, po, plot, pid, **kw):
        k = 'rad40_percent'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('%<sup>40</sup>Ar*', k, ys, po, plot, pid, es, **kw)

    def _plot_kcl(self, po, plot, pid, **kw):
        k = 'kcl'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('K/Cl', k, ys, po, plot, pid, es, **kw)

    def _plot_kca(self, po, plot, pid, **kw):
        k = 'kca'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('K/Ca', k, ys, po, plot, pid, es, **kw)

    def _plot_moles_k39(self, po, plot, pid, **kw):
        k = 'k39'
        ys, es = self._get_aux_plot_data(k)
        return self._plot_aux('K39(fA)', k, ys, po, plot, pid, es, **kw)

    def _get_aux_plot_data(self, k):
        vs = self._unpack_attr(k)
        return [nominal_value(vi) for vi in vs], [std_dev(vi) for vi in vs]

    def _set_ml_title(self, text, plotid, ax):
        plot = self.graph.plots[plotid]
        tag = '{}_axis'.format(ax)
        xa = getattr(plot, tag)
        nxa = MPlotAxis()
        nxa.title = text
        nxa.clone(xa)

        setattr(plot, tag, nxa)

    # ===============================================================================
    #
    # ===============================================================================
    def _add_axis_tool(self, plot, axis):
        t = AxisTool(component=axis)
        plot.tools.append(t)

    def _add_limit_tool(self, plot, orientation):
        t = LimitsTool(component=plot,
                       orientation=orientation)

        o = LimitOverlay(component=plot, tool=t)

        plot.tools.append(t)
        plot.overlays.append(o)
        t.on_trait_change(self._handle_limits, 'limits_updated')

    def _handle_limits(self):
        pass

    def _add_point_labels(self, scatter):
        labels = []

        f = self.options.analysis_label_format

        if not f:
            f = '{aliquot:02d}{step:}'

        for si in self.sorted_analyses:
            ctx = {'aliquot': si.aliquot,
                   'step': si.step,
                   'sample': si.sample}

            x = f.format(**ctx)
            labels.append(x)

        font = self.options.get_formatting_value('label_font', 'label_font')
        ov = PointsLabelOverlay(component=scatter,
                                labels=labels,
                                label_box=self.options.label_box,
                                font=font)
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
                               add_selection=True,
                               value_format=None,
                               additional_info=None,
                               index_tag=None,
                               index_attr=None,
                               convert_index=None,
                               items=None
                               ):
        if add_tool:
            broadcaster = BroadcasterTool()
            scatter.tools.append(broadcaster)
            if add_selection:
                rect_tool = RectSelectionTool(scatter)
                rect_overlay = RectSelectionOverlay(component=scatter,
                                                    tool=rect_tool)

                scatter.overlays.append(rect_overlay)
                broadcaster.tools.append(rect_tool)

            if value_format is None:
                value_format = lambda x: '{:0.5f}'.format(x)

            if convert_index is None:
                convert_index = lambda x: '{:0.3f}'.format(x)

            if items is None:
                items = self.sorted_analyses
            point_inspector = AnalysisPointInspector(scatter,
                                                     analyses=items,
                                                     convert_index=convert_index,
                                                     index_tag=index_tag,
                                                     index_attr=index_attr,
                                                     value_format=value_format,
                                                     additional_info=additional_info)

            pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                       tool=point_inspector)

            scatter.overlays.append(pinspector_overlay)
            broadcaster.tools.append(point_inspector)

            # u = lambda a, b, c, d: self.update_graph_metadata(a, b, c, d)
            scatter.index.on_trait_change(self.update_graph_metadata, 'metadata_changed')

    def update_graph_metadata(self, obj, name, old, new):
        pass
    # ===============================================================================
    # labels
    # ===============================================================================
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

    def _build_label_text(self, x, we, n,
                          total_n=None,
                          mswd_args=None,
                          percent_error=False,
                          sig_figs=3):

        display_n = True
        display_mswd = n >= 2

        if display_n:
            if total_n and n != total_n:
                n = 'n= {}/{}'.format(n, total_n)
            else:
                n = 'n= {}'.format(n)
        else:
            n = ''

        if mswd_args and display_mswd:
            mswd, valid_mswd, _ = mswd_args
            vd = '' if valid_mswd else '*'
            mswd = '{}mswd= {:0.2f}'.format(vd, mswd)
        else:
            mswd = ''

        sx = floatfmt(x, sig_figs)
        swe = floatfmt(we, sig_figs)

        if self.options.index_attr in ('uF', 'Ar40/Ar36'):
            me = u'{} {}{}'.format(sx, PLUSMINUS, swe)
        else:
            age_units = self._get_age_units()
            pe = ''
            if percent_error:
                pe = '({})'.format(format_percent_error(x, we, include_percent_sign=True))

            me = u'{} {}{}{} {}'.format(sx, PLUSMINUS, swe, pe, age_units)

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

    # @on_trait_change('graph:plots:index_mapper:updated')
    # def _handle_index_range(self, obj, name, old, new):
    #
    #     if not isinstance(new, bool):
    #         if new.low == -inf or new.high == inf:
    #             return
    #
    #         if self.suppress_xlimits_update:
    #             return
    #
    #         for p in self.graph.plots:
    #             if p.index_mapper == obj:
    #                 op = self.options.aux_plots[-1]
    #                 op.xlimits = (new.low, new.high)
    #                 # print 'setting xlimits', op.xlimits, op, op.name
    #                 break

    # @on_trait_change('graph:plots:value_mapper:updated')
    # def _handle_value_range(self, obj, name, old, new):
    #     if not isinstance(new, bool):
    #         if self.suppress_ylimits_update:
    #             return
    #
    #         for p in self.graph.plots:
    #             if p.value_mapper == obj:
    #                 plot = p
    #                 title = plot.y_axis.title
    #
    #                 if title in PLOT_MAPPING:
    #                     title = PLOT_MAPPING[title]
    #
    #                 for op in self.options.aux_plots:
    #                     if title.startswith(op.name):
    #                         op.ylimits = (new.low, new.high)
    #                         break
    #                 break

    # ===============================================================================
    # property get/set
    # ===============================================================================
    @cached_property
    def _get_sorted_analyses(self):
        return sorted(self.analyses,
                      key=self._cmp_analyses,
                      reverse=self._reverse_sorted_analyses)

    @cached_property
    def _get_analysis_group(self):
        return self._analysis_group_klass(analyses=self.sorted_analyses)

# ============= EOF =============================================
