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

import math

# ============= enthought library imports =======================
from chaco.array_data_source import ArrayDataSource
from chaco.axis import PlotAxis
from chaco.tools.broadcaster import BroadcasterTool
from chaco.tools.data_label_tool import DataLabelTool
from numpy import Inf, vstack, zeros_like, ma
from traits.api import (
    HasTraits,
    Any,
    Int,
    Str,
    Property,
    Event,
    cached_property,
    List,
    Float,
    Instance,
    TraitError,
)
from uncertainties import std_dev, nominal_value, ufloat

from pychron.core.filtering import filter_ufloats, sigma_filter
from pychron.core.helpers.formatting import (
    floatfmt,
    format_percent_error,
    standard_sigfigsfmt,
)
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.ticks import SparseLogTicks, IntTickGenerator, IntSparseTicks
from pychron.graph.ticks import SparseTicks
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.graph.tools.rect_selection_tool import (
    RectSelectionOverlay,
    RectSelectionTool,
)
from pychron.pipeline.plot.flow_label import FlowDataLabel, FlowPlotLabel
from pychron.pipeline.plot.overlays.points_label_overlay import PointsLabelOverlay
from pychron.pipeline.plot.point_move_tool import OverlayMoveTool
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.pychron_constants import PLUSMINUS, format_mswd


class SelectionFigure(HasTraits):
    graph = Any

    def _set_selected(self, ans, sel):
        for i, a in enumerate(ans):
            if i in sel:
                a.set_temp_status(a.otemp_status if a.otemp_status else "omit")
            else:
                a.set_temp_status("ok")

    def _filter_metadata_changes(self, obj, ans, func=None):
        sel = obj.metadata.get("selections", [])
        self._set_selected(ans, sel)
        if func:
            func(sel)

        return sel


class BaseArArFigure(SelectionFigure):
    use_fixed_height = False
    analyses = Any
    sorted_analyses = Property(depends_on="analyses")

    analysis_group = Property(depends_on="analyses, _analysis_group")
    _analysis_group = Instance(AnalysisGroup)
    _analysis_group_klass = AnalysisGroup

    graph_id = Int
    group_id = Int
    subgroup_id = Int
    ytitle = Str
    title = Str
    xtitle = Str

    replot_needed = Event
    recalculate_event = Event
    suppress_recalculate_event = False

    options = Any

    refresh_unknowns_table = Event
    suppress_ylimits_update = False
    suppress_xlimits_update = False

    xpad = None

    ymas = List
    ymis = List
    xmi = Float
    xma = Float
    data_xma = 0

    _has_formatting_hash = None
    _reverse_sorted_analyses = False

    def finalize_group_overlays(self, figs):
        pass

    def get_update_dict(self):
        return {}

    def build(self, plots, plot_dict=None, row=(0, 0), col=(0, 0)):
        """
        make plots
        """

        graph = self.graph

        if len(plots) > 1 and not self.equi_stack:
            vertical_resize = not all([p.height for p in plots[:-1]])
            graph.vertical_resize = vertical_resize
        else:
            graph.vertical_resize = not plots[0].height

        graph.clear_has_title()

        title = self.title
        if not title:
            title = self.options.title

        nplots = len(plots)

        layout = self.options.layout
        fw = layout.fixed_width
        fh = layout.fixed_height

        # stretch_vertical = layout.stretch_vertical

        if fw and col[1] > 0:
            fw = int(fw / col[1])

        oheights = sum([po.height for po in plots[1:]])

        for i, po in enumerate(plots):
            kw = {"ytitle": po.name}
            if plot_dict:
                kw.update(plot_dict)

            if fw:
                r = ""
                if fh:
                    if i == 0 and not po.height or self.use_fixed_height:
                        height = fh - oheights
                    else:
                        height = po.height

                    if self.use_fixed_height:
                        height = fh - oheights
                else:
                    height = po.height
                    # if i == 0 and stretch_vertical:
                    #     r = 'v'
                kw["bounds"] = [fw, height]
                kw["resizable"] = r
            elif fh:
                kw["resizable"] = "h"
                if i == 0 and not po.height or self.use_fixed_height:
                    height = fh - oheights
                else:
                    height = po.height

                kw["bounds"] = [50, height]
            elif po.height:
                kw["bounds"] = [50, po.height]
                kw["resizable"] = "h"
            else:
                kw["resizable"] = "hv"

            # if self.options.layout.fixed_width:
            #     kw['bounds'] = [self.options.layout.fixed_width, kw['bounds'][1]]
            #     kw['resizable'] = ''

            if i == nplots - 1:
                kw["title"] = title

            if not i and self.ytitle:
                kw["ytitle"] = self.ytitle

            if not po.ytitle_visible:
                kw["ytitle"] = ""

            if self.xtitle:
                kw["xtitle"] = self.xtitle

            kw["padding"] = self.options.get_paddings()

            print(kw, plot_dict)
            p = graph.new_plot(**kw)
            if i == (len(plots) - 1):
                p.title_font = self.options.title_font
            # set a tag for easy identification
            p.y_axis.tag = po.name
            self._setup_plot(i, p, po)

    def post_make(self):
        self._fix_log_axes()

    def post_plot(self, plots, row, col):
        graph = self.graph
        n = len(plots)
        for idx, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            self._apply_aux_plot_options(bool(idx), plotobj, po, row, col)
            # if this not the only plot and not the upper left turn off error info overlay
            if row[1] > 1 or col[1] > 1:
                if col[0] or row[0]:
                    for ov in plotobj.overlays:
                        if isinstance(ov, FlowPlotLabel):
                            ov.visible = False

    def plot(self, *args, **kw):
        pass

    def replot(self, *args, **kw):
        if self.options:
            self.plot(self.options.get_plotable_aux_plots())

    def max_x(self, *args):
        return -Inf

    def min_x(self, *args):
        return Inf

    def mean_x(self, *args):
        return 0

    # private
    def _fix_log_axes(self):
        for i, p in enumerate(self.graph.plots):
            if p.value_scale == "log":
                if p.value_mapper.range.low < 0:
                    ys = self.graph.get_data(plotid=i, axis=1)
                    ys = ys[ys > 0]
                    try:
                        m = 10 ** math.floor(math.log10(min(ys)))
                        p.value_mapper.range.low = m
                    except ValueError:
                        continue

                if hasattr(p, "alt_axis"):
                    p.alt_axis.mapper = p.value_mapper

    def _setup_plot(self, i, pp, po):
        # add limit tools
        self.graph.add_limit_tool(pp, "x", self._handle_xlimits)
        self.graph.add_limit_tool(pp, "y", self._handle_ylimits)

        self.graph.add_axis_tool(pp, pp.x_axis)
        self.graph.add_axis_tool(pp, pp.y_axis)

        pp.value_range.on_trait_change(lambda: self.update_options_limits(i), "updated")
        pp.index_range.on_trait_change(lambda: self.update_options_limits(i), "updated")
        pp.value_range.tight_bounds = False

        # this needs to happen post_plot
        # self._apply_aux_plot_options(pp, po)

    def _apply_aux_plot_options(self, is_bottom_plot, pp, po, row, col):
        options = self.options

        # print('aaa', pp.padding_left, pp.width, pp.outer_width)
        if col[0] > 0:
            pp.padding_left = max(20, int(pp.padding_left * 0.5))

        # print('bbb', pp.padding_left, pp.width, pp.outer_width)

        pp.bgcolor = options.plot_bgcolor
        pp.x_grid.visible = options.use_xgrid
        pp.y_grid.visible = options.use_ygrid

        for k, axis in (("x", pp.x_axis), ("y", pp.y_axis)):
            for attr in ("title_font", "tick_in", "tick_out", "tick_label_formatter"):
                value = getattr(options, "{}{}".format(k, attr))
                try:
                    setattr(axis, attr, value)
                except TraitError as e:
                    print(
                        "error setting attr={},value={} error={}".format(attr, value, e)
                    )

            axis.tick_label_font = getattr(options, "{}tick_font".format(k))

        if row[0] < (row[1] - 1) and not is_bottom_plot:
            pp.x_axis.title = ""
            pp.x_axis.tick_visible = False
            pp.x_axis.tick_label_formatter = lambda x: ""
            pp.padding_bottom = 10

        if po:
            alt_axis = None
            if po.y_axis_right:
                pp.y_axis.orientation = "right"
                pp.y_axis.axis_line_visible = False

            if po.yticks_both_sides:
                if self.group_id == 0 and self.subgroup_id == 0:
                    alt_axis = PlotAxis(
                        pp, orientation="left" if po.y_axis_right else "right"
                    )
                    alt_axis.tick_label_formatter = lambda x: ""
                    alt_axis.axis_line_visible = False
                    alt_axis.tick_in = options.ytick_in
                    alt_axis.tick_out = options.ytick_out
                    pp.underlays.append(alt_axis)
                    pp.alt_axis = alt_axis

            if not po.ytitle_visible or col[0] > 0:
                pp.y_axis.title = ""

            if not po.ytick_visible:
                pp.y_axis.tick_visible = False
                pp.y_axis.tick_label_formatter = lambda x: ""
                if alt_axis and not po.ytitle_visible:
                    alt_axis.tick_visible = False
            else:
                if po.has_fixed_ylimits() and col[0] > 0:
                    pp.y_axis.tick_label_formatter = lambda x: ""

                pp.value_scale = po.scale
                if po.scale == "log":
                    if po.use_sparse_yticks:
                        st = SparseLogTicks(step=po.sparse_yticks_step)
                        pp.value_axis.tick_generator = st
                        pp.value_grid.tick_generator = st
                else:
                    st = None
                    pp.value_axis.tick_interval = po.ytick_interval
                    if po.use_sparse_yticks:
                        if po.use_integer_ticks:
                            st = IntSparseTicks(step=po.sparse_yticks_step)
                        else:
                            st = SparseTicks(step=po.sparse_yticks_step)
                    elif po.use_integer_ticks:
                        st = IntTickGenerator()

                    if st is not None:
                        pp.value_axis.tick_generator = st
                        pp.value_grid.tick_generator = st
                        if alt_axis:
                            alt_axis.tick_generator = st

    def _set_options_format(self, pp):
        # print 'using options format'
        pass

    def _set_selected(self, ans, sel):
        super(BaseArArFigure, self)._set_selected(ans, sel)
        self.refresh_unknowns_table = True

    def _cmp_analyses(self, x):
        return x.timestamp or 0

    def _unpack_attr(
        self, attr, scalar=1, exclude_omit=False, nonsorted=False, ans=None
    ):
        if ans is None:
            ans = self.sorted_analyses

        if nonsorted:
            ans = self.analyses

        def gen():
            for ai in ans:
                if exclude_omit and ai.is_omitted():
                    continue

                v = ai.get_value(attr)
                if v is None:
                    v = ufloat(0, 0)
                yield v * scalar

        return gen()

    def _set_y_limits(self, a, b, min_=None, max_=None, pid=0, pad=None):
        mi, ma = self.graph.get_y_limits(plotid=pid)

        mi = min_ if min_ is not None else min(mi, a)

        ma = max_ if max_ is not None else max(ma, b)

        self.graph.set_y_limits(
            min_=mi, max_=ma, pad=pad, plotid=pid, pad_style="upper"
        )

    def update_options_limits(self, pid):
        if not self.suppress_xlimits_update:
            if hasattr(self.options, "aux_plots"):
                # n = len(self.options.aux_plots)
                xlimits = self.graph.get_x_limits(pid)
                for ap in self.options.aux_plots:
                    ap.xlimits = xlimits

        if not self.suppress_ylimits_update:
            if hasattr(self.options, "aux_plots"):
                # n = len(self.options.aux_plots)
                ylimits = self.graph.get_y_limits(pid)

                for i, ap in enumerate(self.options.get_plotable_aux_plots()):
                    if i == pid:
                        ap.ylimits = ylimits
                        break

                # for ap in self.options.aux_plots:
                #     ap.ylimits = ylimits

                # ap = self.options.aux_plots[n - pid - 1]
                # if not self.suppress_ylimits_update:
                #     ap.ylimits = self.graph.get_y_limits(pid)

                # if not self.suppress_xlimits_update:
                #     ap.xlimits = self.graph.get_x_limits(pid)
                #     print('asdfpasdf', id(self.options), id(ap), ap.xlimits)

    def get_valid_xbounds(self):
        pass

    # ===========================================================================
    # aux plots
    # ===========================================================================
    def _do_aux_plot_filtering(self, scatter, po, vs, es):
        omits, invalids, outliers = [], [], []
        if po.filter_str:
            omits, invalids, outliers = self._get_aux_plot_filtered(po, vs, es)
            for idx, item in enumerate(self.sorted_analyses):
                if idx in omits:
                    s = "omit"
                elif idx in invalids:
                    s = "invalid"
                elif idx in outliers:
                    s = "outlier"
                else:
                    s = "ok"
                item.set_temp_status(s)

        return omits, invalids, outliers

    def _get_aux_plot_filtered(self, po, vs, es=None):
        omits = []
        invalids = []
        outliers = []

        fs = po.filter_str
        nsigma = po.sigma_filter_n
        if fs or nsigma:
            if es is None:
                es = zeros_like(vs)
            ufs = vstack((vs, es)).T
            filter_str_idx = None
            if fs:
                filter_str_idx = filter_ufloats(ufs, fs)
                ftag = po.filter_str_tag.lower()

                if ftag == "invalid":
                    invalids.extend(filter_str_idx)
                elif ftag == "outlier":
                    outliers.extend(filter_str_idx)
                else:
                    omits.extend(filter_str_idx)

            if nsigma:
                vs = ma.array(vs, mask=False)
                if filter_str_idx is not None:
                    vs.mask[filter_str_idx] = True
                sigma_idx = sigma_filter(vs, nsigma)

                stag = po.sigma_filter_tag.lower()
                if stag == "invalid":
                    invalids.extend(sigma_idx)
                elif stag == "outlier":
                    outliers.extend(sigma_idx)
                else:
                    omits.extend(sigma_idx)

        return omits, invalids, outliers

    def _plot_raw_40_36(self, po, pid):
        return self._plot_aux("uAr40/Ar36", po, pid)

    def _plot_ic_40_36(self, po, pobj, pid):
        return self._plot_aux("Ar40/Ar36", po, pid)

    def _plot_icf_40_36(self, po, pobj, pid):
        return self._plot_aux("icf_40_36", po, pid)

    def _plot_radiogenic_yield(self, po, pobj, pid):
        return self._plot_aux("radiogenic_yield", po, pid)

    def _plot_kcl(self, po, pobj, pid):
        return self._plot_aux("kcl", po, pid)

    def _plot_clk(self, po, pobj, pid):
        return self._plot_aux("clk", po, pid)

    def _plot_kca(self, po, pobj, pid):
        return self._plot_aux("kca", po, pid)

    def _plot_signal_k39(self, po, pobj, pid):
        return self._plot_aux("k39", po, pid)

    def _plot_moles_k39(self, po, pobj, pid):
        return self._plot_aux("moles_k39", po, pid)

    def _plot_moles_ar40(self, po, pobj, pid):
        return self._plot_aux("Ar40", po, pid)

    def _plot_moles_ar36(self, po, pobj, pid):
        return self._plot_aux("Ar36", po, pid)

    def _plot_extract_value(self, po, pobj, pid):
        return self._plot_aux("extract_value", po, pid)

    def _get_aux_plot_data(self, k, scalar=1):
        vs = list(self._unpack_attr(k, scalar=scalar))
        return [nominal_value(vi) for vi in vs], [std_dev(vi) for vi in vs]

    def _handle_ylimits(self):
        pass

    def _handle_xlimits(self):
        pass

    def _add_point_labels(self, scatter, ans=None):
        f = self.options.analysis_label_format
        if not f:
            f = "{aliquot:02d}{step:}"

        if ans is None:
            ans = self.sorted_analyses

        labels = [
            f.format(
                aliquot=si.aliquot,
                step=si.step,
                sample=si.sample,
                name=si.name,
                label_name=si.label_name,
                runid=si.record_id,
            )
            for si in ans
        ]

        font = self.options.label_font
        ov = PointsLabelOverlay(
            component=scatter,
            labels=labels,
            label_box=self.options.label_box,
            font=font,
        )
        scatter.underlays.append(ov)

    def _add_error_bars(
        self, scatter, errors, axis, nsigma, line_width=1, end_caps=True, visible=True
    ):
        ebo = ErrorBarOverlay(
            component=scatter,
            orientation=axis,
            nsigma=nsigma,
            visible=visible,
            line_width=line_width,
            use_end_caps=end_caps,
        )

        scatter.underlays.append(ebo)
        setattr(scatter, "{}error".format(axis), ArrayDataSource(errors))
        return ebo

    def _add_scatter_inspector(
        self,
        scatter,
        inspector=None,
        add_tool=True,
        add_selection=True,
        value_format=None,
        additional_info=None,
        index_tag=None,
        index_attr=None,
        convert_index=None,
        items=None,
        update_meta_func=None,
    ):
        if add_tool:
            # broadcaster = BroadcasterTool()
            # scatter.tools.append(broadcaster)

            if inspector is None:
                if value_format is None:

                    def value_format(x):
                        return "{:0.5f}".format(x)

                if convert_index is None:

                    def convert_index(x):
                        return "{:0.3f}".format(x)

                if items is None:
                    items = self.sorted_analyses
                inspector = AnalysisPointInspector(
                    scatter,
                    use_pane=False,
                    analyses=items,
                    convert_index=convert_index,
                    index_tag=index_tag,
                    index_attr=index_attr,
                    value_format=value_format,
                    additional_info=additional_info,
                )

                pinspector_overlay = PointInspectorOverlay(
                    component=scatter, tool=inspector
                )
                scatter.overlays.append(pinspector_overlay)
                # broadcaster.tools.append(inspector)
                scatter.tools.append(inspector)
            else:
                if not isinstance(inspector, (list, tuple)):
                    inspector = (inspector,)

                for i in inspector:
                    # broadcaster.tools.append(i)
                    scatter.tools.append(i)
                    # # pinspector_overlay = PointInspectorOverlay(component=scatter,
                    # #                                            tool=point_inspector)
                    # # print 'fff', inspector
                    #
                    # event_queue = {}
                    # for i in inspector:
                    #     i.event_queue = event_queue
                    #     i.on_trait_change(self._handle_inspection, 'inspector_item')
                    #     # scatter.overlays.append(pinspector_overlay)
                    #     broadcaster.tools.append(i)
            if add_selection:
                rect_tool = RectSelectionTool(scatter)
                rect_overlay = RectSelectionOverlay(component=scatter, tool=rect_tool)

                scatter.overlays.append(rect_overlay)
                # broadcaster.tools.append(rect_tool)
                scatter.tools.append(rect_tool)

            if update_meta_func is None:
                update_meta_func = self.update_graph_metadata
            # u = lambda a, b, c, d: self.update_graph_metadata(a, b, c, d)
            scatter.index.on_trait_change(update_meta_func, "metadata_changed")

    def update_graph_metadata(self, obj, name, old, new):
        pass

    # ===============================================================================
    # labels
    # ===============================================================================
    def _add_info_label(self, plot, text_lines, font=None):
        if font is None:
            font = self.options.error_info_font

        ov = FlowPlotLabel(
            text="\n".join(text_lines),
            overlay_position="inside top",
            padx=3,
            pady=-3,
            hjustify="left",
            bgcolor=plot.bgcolor,
            border_visible=False,
            font=font,
            component=plot,
        )
        plot.overlays.append(ov)
        plot.tools.append(OverlayMoveTool(component=ov))

    def _add_data_label(
        self,
        s,
        text,
        point,
        bgcolor="transparent",
        label_position="top right",
        color=None,
        append=True,
        **kw
    ):
        if color is None:
            color = s.color

        label = FlowDataLabel(
            component=s,
            data_point=point,
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
            **kw
        )
        s.overlays.append(label)
        tool = DataLabelTool(label)
        if append:
            label.tools.append(tool)
        else:
            label.tools.insert(0, tool)

        label.on_trait_change(self._handle_overlay_move, "label_position")
        return label

    def _build_n_label_text(self, n):
        total_n = self.analysis_group.total_n
        n = "n = {}".format(n)
        if total_n and n != total_n:
            n = "{}/{}".format(n, total_n)
        return n

    def _build_label_text(
        self,
        x,
        we,
        n,
        mswd_args=None,
        display_n=True,
        display_mswd=True,
        display_mswd_pvalue=False,
        percent_error=False,
        sig_figs=3,
        mswd_sig_figs=3,
    ):
        display_mswd = n >= 2 and display_mswd

        if display_n:
            n = self._build_n_label_text(n)
        else:
            n = ""

        if mswd_args and display_mswd:
            mswd, valid_mswd, _, pvalue = mswd_args
            mswd = format_mswd(mswd, valid_mswd, n=mswd_sig_figs, include_tag=True)
            if display_mswd_pvalue:
                mswd = "{} pvalue = {:0.2f}".format(mswd, pvalue)
        else:
            mswd = ""

        if sig_figs == "Std":
            sx, swe = standard_sigfigsfmt(x, we)
        else:
            sx = floatfmt(x, sig_figs)
            swe = floatfmt(we, sig_figs)

        if self.options.index_attr in ("uF", "Ar40/Ar36"):
            me = "{} {} {}".format(sx, PLUSMINUS, swe)
        else:
            age_units = self._get_age_units()
            pe = ""
            if percent_error:
                pe = "({})".format(
                    format_percent_error(x, we, include_percent_sign=True)
                )

            me = "{} {} {}{} {}".format(sx, PLUSMINUS, swe, pe, age_units)

        return "{} {} {}".format(me, mswd, n)

    def _get_age_units(self):
        a = "Ma"
        if self.analyses:
            a = self.analyses[0].arar_constants.age_units
        return a

    def _set_renderer_selection(self, rs, sel):
        meta = {"selections": sel}
        for rend in rs:
            rend.index.trait_set(metadata=meta)

    def _handle_label_move(self, obj, name, old, new):
        axps = [a for a in self.options.aux_plots if a.plot_enabled][::-1]
        for i, p in enumerate(self.graph.plots):
            if next((pp for pp in p.plots.values() if obj.component == pp[0]), None):
                axp = axps[i]
                if hasattr(new, "__iter__"):
                    new = [float(ni) for ni in new]
                else:
                    new = float(new)
                axp.set_overlay_position(obj.id, new)

    def _handle_overlay_move(self, obj, name, old, new):
        axps = [a for a in self.options.aux_plots if a.plot_enabled][::-1]
        for i, p in enumerate(self.graph.plots):
            if next((pp for pp in p.plots.values() if obj.component == pp[0]), None):
                axp = axps[i]
                if hasattr(new, "__iter__"):
                    new = [float(ni) for ni in new]
                else:
                    new = float(new)
                axp.set_overlay_position(obj.id, new)

                break

    def _analysis_group_hook(self, ag):
        pass

    # ===============================================================================
    # property get/set
    # ===============================================================================
    @cached_property
    def _get_sorted_analyses(self):
        return sorted(
            self.analyses, key=self._cmp_analyses, reverse=self._reverse_sorted_analyses
        )

    @cached_property
    def _get_analysis_group(self):
        ag = self._analysis_group
        if ag is None:
            ag = self._analysis_group_klass(
                group_id=self.group_id,
                analyses=self.sorted_analyses,
                omit_by_tag=self.options.omit_by_tag,
            )
            self._analysis_group_hook(ag)

        return ag

    def _set_analysis_group(self, v):
        self._analysis_group = v


# ============= EOF =============================================
