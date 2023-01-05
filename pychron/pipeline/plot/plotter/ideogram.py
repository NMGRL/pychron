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
import math
from operator import itemgetter

from chaco.abstract_overlay import AbstractOverlay
from chaco.array_data_source import ArrayDataSource
from chaco.data_label import DataLabel
from chaco.scatterplot import render_markers
from chaco.tooltip import ToolTip
from enable.colors import ColorTrait
from numpy import array, arange, Inf, argmax, asarray
from pyface.message_dialog import warning
from traits.api import Array
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.stats import calculate_weighted_mean
from pychron.core.stats.peak_detection import fast_find_peaks
from pychron.core.stats.probability_curves import cumulative_probability, kernel_density
from pychron.graph.explicit_legend import ExplicitLegend
from pychron.graph.ticks import IntTickGenerator
from pychron.pipeline.plot.overlays.correlation_ellipses_overlay import (
    CorrelationEllipsesOverlay,
)
from pychron.pipeline.plot.overlays.ideogram_inset_overlay import (
    IdeogramInset,
    IdeogramPointsInset,
)
from pychron.pipeline.plot.overlays.mean_indicator_overlay import MeanIndicatorOverlay
from pychron.pipeline.plot.overlays.subgroup_overlay import SubGroupPointOverlay
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
from pychron.pipeline.plot.point_move_tool import OverlayMoveTool
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup
from pychron.processing.interpreted_age import InterpretedAge
from pychron.pychron_constants import (
    PLUSMINUS,
    SIGMA,
    KERNEL,
    SCHAEN2020_3,
    SCHAEN2020_2,
    SCHAEN2020_1,
    DEINO,
    SCHAEN2020_3youngest,
)
from pychron.regex import ORDER_PREFIX_REGEX

N = 500


class PeakLabel(DataLabel):
    show_label_coords = False
    border_visible = False

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        # if self.clip_to_plot:
        #     gc.save_state()
        #     c = component
        #     gc.clip_to_rect(c.x, c.y, c.width, c.height)

        self.do_layout()

        # if self.label_style == 'box':
        self._render_box(component, gc, view_bounds=view_bounds, mode=mode)
        # else:
        #     self._render_bubble(component, gc, view_bounds=view_bounds,
        #                         mode=mode)

    def _render_box(self, component, gc, view_bounds=None, mode="normal"):
        # draw the arrow if necessary
        # if self.arrow_visible:
        #     if self._cached_arrow is None:
        #         if self.arrow_root in self._root_positions:
        #             ox, oy = self._root_positions[self.arrow_root]
        #         else:
        #             if self.arrow_root == "auto":
        #                 arrow_root = self.label_position
        #             else:
        #                 arrow_root = self.arrow_root
        #             pos = self._position_root_map.get(arrow_root, "DUMMY")
        #             ox, oy = self._root_positions.get(pos,
        #                                 (self.x + self.width / 2,
        #                                  self.y + self.height / 2))
        #
        #         if type(ox) == str:
        #             ox = getattr(self, ox)
        #             oy = getattr(self, oy)
        #         self._cached_arrow = draw_arrow(gc, (ox, oy),
        #                                     self._screen_coords,
        #                                     self.arrow_color_,
        #                                     arrowhead_size=self.arrow_size,
        #                                     offset1=3,
        #                                     offset2=self.marker_size + 3,
        #                                     minlen=self.arrow_min_length,
        #                                     maxlen=self.arrow_max_length)
        #     else:
        #         draw_arrow(gc, None, None, self.arrow_color_,
        #                    arrow=self._cached_arrow,
        #                    minlen=self.arrow_min_length,
        #                    maxlen=self.arrow_max_length)

        # layout and render the label itself
        ToolTip.overlay(self, component, gc, view_bounds, mode)


class LatestOverlay(AbstractOverlay):
    data_position = None
    color = ColorTrait("transparent")

    # The color of the outline to draw around the marker.
    outline_color = ColorTrait("orange")

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            pts = self.component.map_screen(self.data_position)
            render_markers(gc, pts, "circle", 5, self.color_, 2, self.outline_color_)


def groupby_aux_key(ans):
    use_explicit_ordering = all(
        (ORDER_PREFIX_REGEX.match(str(a.aux_name or "")) for a in ans)
    )
    if use_explicit_ordering:

        def key(ai):
            m = ORDER_PREFIX_REGEX.match(ai.aux_name)
            return int(m.group("prefix")[:-1])

    else:
        key = "aux_id"

    gitems = groupby_key(ans, key=key)
    gitems = [(a, list(b)) for a, b in gitems]

    for i, (gid, analyses) in enumerate(gitems):
        for ai in analyses:
            ai.aux_id = i

    return gitems, use_explicit_ordering


class Ideogram(BaseArArFigure):
    xs = Array
    xes = Array
    ytitle = "Relative Probability"

    subgroup = None
    peaks = None

    def plot(self, plots, legend=None):
        """
        plot data on plots
        """
        opt = self.options
        index_attr = opt.index_attr
        if index_attr:
            if index_attr == "uage" and opt.include_j_position_error:
                index_attr = "uage_w_position_err"

        else:
            warning(None, "X Value not set. Defaulting to Age")
            index_attr = "uage"

        graph = self.graph

        try:
            xs, es = array(
                [
                    (nominal_value(ai), std_dev(ai))
                    for ai in self._get_xs(key=index_attr)
                ]
            ).T

            xs = self.normalize(xs, es)
            self.xs = xs
            self.xes = es
        except (ValueError, AttributeError) as e:
            print("asdfasdf", e, index_attr)
            import traceback

            traceback.print_exc()
            return

        # if self.options.omit_by_tag:
        selection = []
        mck = opt.mean_calculation_kind
        if mck in [
            SCHAEN2020_1,
            SCHAEN2020_2,
            SCHAEN2020_3,
            SCHAEN2020_3youngest,
            DEINO,
        ]:
            self.analysis_group.clear_temp_selected()
            selection = self.analysis_group.get_outliers(mck, **opt.outlier_options)

        selection = list(
            set(
                selection + self.analysis_group.get_omitted_by_tag(self.sorted_analyses)
            )
        )

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            if opt.reverse_x_axis:
                plotobj.default_origin = "bottom right"

            plot_name = po.plot_name
            if not plot_name:
                continue

            try:
                args = getattr(self, "_plot_{}".format(plot_name))(po, plotobj, pid)
            except AttributeError:
                import traceback

                traceback.print_exc()
                continue

            if args:
                scatter, aux_selection, invalid = args
                selection.extend(aux_selection)

        t = index_attr
        if index_attr == "uF":
            t = "Ar40*/Ar39k"
        elif index_attr in ("uage", "uage_w_position_err"):
            ref = self.analyses[0]
            age_units = ref.arar_constants.age_units
            t = "Age ({})".format(age_units)

        graph.set_x_title(t, plotid=0)

        # turn off ticks for prob plot by default
        plot = graph.plots[0]
        plot.value_axis.tick_label_formatter = lambda x: ""
        plot.value_axis.tick_visible = False

        self._rebuild_ideo(selection)

    def mean_x(self, attr):
        # todo: handle other attributes
        return nominal_value(self.analysis_group.weighted_age)

    def max_x(self, *args, **kw):
        # try:
        #     return max([nominal_value(ai) + std_dev(ai) * 2
        #                 for ai in self._unpack_attr(attr, exclude_omit=exclude_omit) if ai is not None])
        # except (AttributeError, ValueError) as e:
        #     print('max', e, 'attr={}'.format(attr))
        #     return 0
        return max(self._min_max(*args, **kw))

    def min_x(self, *args, **kw):
        return min(self._min_max(sign=-1, *args, **kw))

    def _min_max(self, attr, sign=1, exclude_omit=False):
        try:
            ans = [
                ai
                for ai in self._unpack_attr(attr, exclude_omit=exclude_omit)
                if ai is not None
            ]
            xs = [nominal_value(ai) + sign * std_dev(ai) * 2 for ai in ans]
            es = [std_dev(ai) for ai in ans]
            xs = self.normalize(xs, es)
            return xs
        except (AttributeError, ValueError) as e:
            print("min max", e)
            return 0

    def get_valid_xbounds(self):
        l, h = self.min_x(self.options.index_attr, exclude_omit=True), self.max_x(
            self.options.index_attr, exclude_omit=True
        )
        return l, h

    def update_index_mapper(self, obj, name, old, new):
        self._rebuild_ideo()
        # if new:
        #     self.update_graph_metadata(None, name, old, new)

    def update_graph_metadata(self, obj, name, old, new):
        if hasattr(obj, "suppress_update") and obj.suppress_update:
            return

        ans = self.sorted_analyses
        sel = obj.metadata.get("selections", [])
        self._set_selected(ans, sel)
        self._rebuild_ideo(sel)
        self.recalculate_event = True

        # self._filter_metadata_changes(obj, sorted_ans, self._rebuild_ideo)

    def get_ybounds(self):
        plot = self.graph.plots[0]
        gid = self.group_id + 1
        try:
            lp = plot.plots["Current-{}".format(gid)][0]
            h = lp.value.get_data().max()
        except KeyError:
            h = 1

        return 0, h

    def replot(self):
        self._rebuild_ideo()

    def normalize(self, xs, es):
        xs = asarray(xs)
        opt = self.options
        if opt.age_normalize:
            offset = opt.age_normalize_value
            if not offset:
                offset, _ = calculate_weighted_mean(xs, es)
            xs -= offset

            print("asfd", offset)
        print(xs)
        return xs

    # ===============================================================================
    # plotters
    # ===============================================================================
    def _get_aux_plot_data(self, k, scalar=1):
        def gen():
            items, ordering = groupby_aux_key(self.sorted_analyses)
            for aux_id, ais in items:
                ais = list(ais)
                xs, xes = zip(
                    *[
                        (nominal_value(vi), std_dev(vi))
                        for vi in self._unpack_attr(self.options.index_attr, ans=ais)
                    ]
                )
                xs = self.normalize(xs, xes)
                ys, yes = zip(
                    *[
                        (nominal_value(vi), std_dev(vi))
                        for vi in self._unpack_attr(k, ans=ais, scalar=scalar)
                    ]
                )

                m = ORDER_PREFIX_REGEX.match(ais[0].aux_name)
                if m:
                    aux_id = int(m.group("prefix")[:-1])

                yield aux_id, ais, xs, xes, ys, yes

        return gen()

    def _plot_aux(self, vk, po, pid):
        title = po.get_ytitle(vk)

        for aux_id, items, xs, xes, ys, yes in self._get_aux_plot_data(vk, po.scalar):
            scatter = self._add_aux_plot(
                ys, title, po, pid, gid=self.group_id or aux_id, es=yes, xs=xs
            )
            nsigma = self.options.error_bar_nsigma
            if xes:
                self._add_error_bars(
                    scatter,
                    xes,
                    "x",
                    nsigma,
                    end_caps=self.options.x_end_caps,
                    line_width=self.options.error_bar_line_width,
                    visible=po.x_error,
                )
            if yes:
                self._add_error_bars(
                    scatter,
                    yes,
                    "y",
                    nsigma,
                    end_caps=self.options.y_end_caps,
                    line_width=self.options.error_bar_line_width,
                    visible=po.y_error,
                )

            if po.show_labels:
                self._add_point_labels(scatter, ans=items)
            if self.options.show_subgroup_indicators:
                self._add_subgroup_overlay(scatter, items)

            func = self._get_index_attr_label_func()
            self._add_scatter_inspector(scatter, items=items, additional_info=func)

        # return scatter, selection, invalid

    def _plot_analysis_number(self, *args, **kw):
        return self.__plot_analysis_number(*args, **kw)

    def _plot_analysis_number_nonsorted(self, *args, **kw):
        kw["nonsorted"] = True
        return self.__plot_analysis_number(*args, **kw)

    def __plot_analysis_number(self, po, plot, pid, nonsorted=False):
        opt = self.options
        index_attr = opt.index_attr
        if index_attr == "uage" and opt.include_j_position_error:
            index_attr = "uage_w_position_err"

        if nonsorted:
            # ytitle = 'A# Nonsorted'
            tag = "Analysis Number Nonsorted"
            # xs = [nominal_value(x) for x in self._get_xs(key=index_attr, nonsorted=True)]
        else:
            # ytitle = 'Analysis #'
            tag = "Analysis Number"
            # xs = self.xs
        ytitle = po.get_ytitle(tag)
        # selection = []

        startidx = 1
        for p in self.graph.plots:
            # if title is not visible title=='' so check tag instead
            if p.y_axis.tag == tag:
                for k, rend in p.plots.items():
                    # if title is not visible k == e.g '-1' instead of 'Analysis #-1'
                    if k.startswith(ytitle) or k.startswith("-"):
                        startidx += rend[0].index.get_size()

        items = self.sorted_analyses
        ats = array([ai.timestamp or 0 for ai in items])

        gitems, use_explicit_ordering = groupby_aux_key(items)

        if not nonsorted:
            gitems = [(a, list(b)) for a, b in gitems]
            if use_explicit_ordering:

                def key(x):
                    return x[0]

            else:

                def key(x):
                    return min(xi.age for xi in x[1])

            gitems = sorted(gitems, key=key)

            if not use_explicit_ordering:
                if opt.analysis_number_sorting != "Oldest @Top":
                    gitems = reversed(gitems)

        global_sorting = opt.global_analysis_number_sorting

        if global_sorting:
            n = len(items)
            if opt.analysis_number_sorting == "Oldest @Top" or nonsorted:
                gys = arange(startidx, startidx + n)
            else:
                gys = arange(startidx + n - 1, startidx - 1, -1)

        plots = {}
        labels = []
        gla = opt.group_legend_label_attribute
        for aux_id, ais in gitems:
            ais = list(ais)
            n = len(ais)

            if not global_sorting:
                if opt.analysis_number_sorting == "Oldest @Top" or nonsorted:
                    ys = arange(startidx, startidx + n)
                else:
                    ys = arange(startidx + n - 1, startidx - 1, -1)
            else:
                idxs = [items.index(ai) for ai in ais]
                if opt.analysis_number_sorting != "Oldest @Top":
                    idxs = reversed(idxs)
                ys = [gys[idx] for idx in idxs]

            xs, xes = zip(
                *(
                    (nominal_value(xi), std_dev(xi))
                    for xi in self._unpack_attr(index_attr, ans=ais)
                )
            )
            xs = self.normalize(xs, xes)

            startidx += n + 1
            kw = {}
            if opt.use_cmap_analysis_number:
                ts = array([ai.timestamp or 0 for ai in ais])
                ts -= ats[0]
                kw = dict(
                    colors=ts,
                    color_map_name=opt.cmap_analysis_number,
                    type="cmap_scatter",
                    xs=xs,
                )
            else:
                if nonsorted:
                    data = sorted(zip(xs, ys), key=lambda x: x[0])
                    xs, ys = list(zip(*data))

            scatter = self._add_aux_plot(
                ys,
                ytitle,
                po,
                pid,
                gid=max(0, self.group_id or (aux_id - 1)),
                xs=xs,
                **kw
            )

            if opt.include_group_legend:
                key = str(aux_id)
                plots[key] = [scatter]
                if gla == "Group":
                    label = key
                else:
                    label = getattr(ais[0], gla.lower().replace(" ", "_"))

                m = ORDER_PREFIX_REGEX.match(label)
                sortkey = label
                if m:
                    label = m.group("label")
                    sortkey = int(m.group("prefix")[:-1])

                labels.append((key, label, sortkey))

            if opt.use_latest_overlay:
                idx = argmax(ts)
                dx = scatter.index.get_data()[idx]
                dy = scatter.value.get_data()[idx]

                scatter.overlays.append(
                    LatestOverlay(component=scatter, data_position=array([(dx, dy)]))
                )
            self._add_error_bars(
                scatter,
                xes,
                "x",
                opt.error_bar_nsigma,
                line_width=self.options.error_bar_line_width,
                end_caps=opt.x_end_caps,
                visible=po.x_error,
            )

            if po.show_labels:
                self._add_point_labels(scatter, ans=ais)

            if self.options.show_subgroup_indicators:
                self._add_subgroup_overlay(scatter, ais)

            # set tick generator
            gen = IntTickGenerator()
            plot.y_axis.tick_generator = gen
            plot.y_grid.tick_generator = gen

            my = max(ys) + 1
            plot.value_range.tight_bounds = True
            self._set_y_limits(0, my, min_=0, max_=my, pid=pid)

            func = self._get_index_attr_label_func()
            self._add_scatter_inspector(
                scatter,
                items=ais,
                value_format=lambda x: "{:d}".format(int(x)),
                additional_info=func,
            )

        if opt.include_group_legend:
            labels = sorted(labels, key=itemgetter(2))
            self._add_group_legend(plot, plots, labels)
            # omits, invalids, outliers = self._do_aux_plot_filtering(scatter, po, xs, xes)
            # selection = omits + outliers
            # selection.extend(omits)
            # selection.extend(outliers)

    def _add_subgroup_overlay(self, scatter, ans):
        idx = [i for i, a in enumerate(ans) if isinstance(a, InterpretedAgeGroup)]
        if idx:
            o = SubGroupPointOverlay(component=scatter, indexes=idx)
            scatter.overlays.append(o)

    def _get_index_attr_label_func(self):
        ia = self.options.index_attr
        if ia.startswith("uage"):
            name = "Age"
            ia = "uage"
            if self.options.include_j_position_error:
                ia = "uage_w_position_err"
        else:
            name = ia

        return lambda i, x, y, ai: "{}= {}".format(name, ai.value_string(ia))

    def _plot_relative_probability(self, po, plot, pid):
        graph = self.graph
        bins, probs = self._calculate_probability_curve(
            self.xs, self.xes, calculate_limits=True
        )

        ogid = self.group_id
        gid = ogid + 1
        sgid = ogid * 2
        plotkw = self.options.get_plot_dict(ogid, self.subgroup_id)

        line, _ = graph.new_series(x=bins, y=probs, plotid=pid, **plotkw)
        line.history_id = self.group_id

        self._add_peak_labels(line, self.xs)

        graph.set_series_label("Current-{}".format(gid), series=sgid, plotid=pid)

        # add the dashed original line
        dline, _ = graph.new_series(
            x=bins,
            y=probs,
            plotid=pid,
            visible=False,
            color=line.color,
            line_style="dash",
        )
        dline.history_id = self.group_id

        graph.set_series_label("Original-{}".format(gid), series=sgid + 1, plotid=pid)

        self._add_info(graph, plot)
        self._add_mean_indicator(graph, line, po, bins, probs, pid)

        mi, ma = min(probs), max(probs)
        self._set_y_limits(mi, ma, min_=0, pad="0.025")

        # d = lambda a, b, c, d: self.update_index_mapper(a, b, c, d)
        # if ogid == 0:
        plot.index_mapper.range.on_trait_change(self.update_index_mapper, "updated")

        if self.options.display_inset:
            xs = self.xs
            n = xs.shape[0]

            startidx = 1
            if self.group_id > 0:
                for ov in plot.overlays:
                    if isinstance(ov, IdeogramPointsInset):
                        print(
                            "ideogram point inset",
                            self.group_id,
                            startidx,
                            ov.value.get_bounds()[1] + 1,
                        )
                        startidx = max(startidx, ov.value.get_bounds()[1] + 1)
            else:
                startidx = 1

            if self.options.analysis_number_sorting == "Oldest @Top":
                ys = arange(startidx, startidx + n)
            else:
                ys = arange(startidx + n - 1, startidx - 1, -1)

            yma2 = max(ys) + 1
            h = self.options.inset_height / 2.0
            if self.group_id == 0:
                bgcolor = self.options.plot_bgcolor
            else:
                bgcolor = "transparent"

            d = self.options.get_plot_dict(ogid, self.subgroup_id)
            o = IdeogramPointsInset(
                self.xs,
                ys,
                color=d["color"],
                outline_color=d["color"],
                bgcolor=bgcolor,
                width=self.options.inset_width,
                height=h,
                visible_axes=False,
                xerror=ArrayDataSource(self.xes),
                location=self.options.inset_location,
            )
            plot.overlays.append(o)

            def cfunc(x1, x2):
                return cumulative_probability(self.xs, self.xes, x1, x2, n=N)

            xs, ys, xmi, xma = self._calculate_asymptotic_limits(
                cfunc, tol=self.options.asymptotic_height_percent
            )
            oo = IdeogramInset(
                xs,
                ys,
                color=d["color"],
                bgcolor=bgcolor,
                yoffset=h,
                visible_axes=self.group_id == 0,
                width=self.options.inset_width,
                height=self.options.inset_height,
                location=self.options.inset_location,
            )

            yma = max(ys)
            if self.group_id > 0:
                for ov in plot.overlays:
                    if isinstance(ov, IdeogramInset):
                        mi, ma = ov.get_x_limits()
                        xmi = min(mi, xmi)
                        xma = max(ma, xma)

                        _, ma = ov.get_y_limits()
                        yma = max(ma, yma)

            plot.overlays.append(oo)
            for ov in plot.overlays:
                if isinstance(ov, IdeogramInset):
                    ov.set_x_limits(xmi, xma)
                    ov.set_y_limits(0, yma * 1.1)
                elif isinstance(ov, IdeogramPointsInset):
                    ov.set_x_limits(xmi, xma)
                    ov.set_y_limits(0, yma2)

    def _add_group_legend(self, plot, plots, labels):

        ln, ns, _ = zip(*labels)
        labels = list(zip(ln, ns))

        legend = ExplicitLegend(
            plots=plots, labels=list(reversed(labels)), inside=True, align="ul"
        )

        plot.overlays.append(legend)

    def _add_peak_labels(self, line, fxs):
        opt = self.options

        xs = line.index.get_data()
        ys = line.value.get_data()
        if xs.shape[0]:
            xp, yp, xr = fast_find_peaks(ys, xs)
            ntxt = ""
            for xmin, xmax in xr:
                ans = [a for a in fxs if xmin <= a <= xmax]
                n = len(ans)
                ntxt = " n={}".format(n)

            self.peaks = xp

            if opt.label_all_peaks:
                border = opt.peak_label_border
                border_color = opt.peak_label_border_color

                bgcolor = (
                    opt.peak_label_bgcolor
                    if opt.peak_label_bgcolor_enabled
                    else "transparent"
                )

                for xi, yi in zip(xp, yp):
                    p = floatfmt(xi, n=opt.peak_label_sigfigs)
                    txt = "{}{}".format(p, ntxt)
                    label = PeakLabel(
                        line,
                        data_point=(xi, yi),
                        label_text=txt,
                        border_visible=bool(border),
                        border_width=border,
                        border_color=border_color,
                        bgcolor=bgcolor,
                    )
                    line.overlays.append(label)

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = []
                if self.options.show_mean_info:
                    m = self.options.mean_calculation_kind
                    s = self.options.nsigma
                    es = self.options.error_bar_nsigma
                    ts.append(
                        "Mean: {} {} {}{} Data: {} {}{}".format(
                            m, PLUSMINUS, s, SIGMA, PLUSMINUS, es, SIGMA
                        )
                    )
                if self.options.show_error_type_info:
                    ts.append("Error Type: {}".format(self.options.error_calc_method))

                if ts:
                    self._add_info_label(plot, ts)

    def _add_mean_indicator(self, g, line, po, bins, probs, pid):
        wm, we, mswd, valid_mswd, n, pvalue = self._calculate_stats(bins, probs)
        ogid = self.group_id
        gid = ogid + 1

        opt = self.options
        text = ""
        if opt.display_mean:
            mswd_args = None
            if opt.display_mean_mswd:
                mswd_args = (mswd, valid_mswd, n, pvalue)

            text = self._make_mean_label(wm, we * opt.nsigma, n, mswd_args)

        plotkw = opt.get_plot_dict(ogid, self.subgroup_id)

        m = MeanIndicatorOverlay(
            component=line,
            x=wm,
            y=20 * gid,
            error=we,
            nsigma=opt.nsigma,
            color=plotkw["color"],
            group_marker=plotkw.get("marker", "circle"),
            group_marker_size=plotkw.get("marker_size", 1),
            display_group_marker=opt.display_group_marker,
            group_id=gid,
            location=opt.display_mean_location,
            visible=opt.display_mean_indicator,
            id="mean_{}".format(self.group_id),
        )

        font = opt.mean_indicator_font
        m.font = str(font).lower()
        m.text = text

        line.overlays.append(m)

        line.tools.append(OverlayMoveTool(component=m, constrain="x"))

        m.on_trait_change(self._handle_overlay_move, "altered_screen_point")

        if m.id in po.overlay_positions:
            ap = po.overlay_positions[m.id]
            m.y = ap[1]

        if m.label:
            m.label.on_trait_change(self._handle_label_move, "altered_screen_point")
            if m.label.id in po.overlay_positions:
                ap = po.overlay_positions[m.label.id]
                m.label.altered_screen_point = (ap[0], ap[1])
                m.label.trait_set(x=ap[0], y=ap[1])

        return m

    def _rebuild_ideo(self, sel=None):
        graph = self.graph
        gid = self.group_id + 1

        plot = graph.plots[0]
        try:
            lp = plot.plots["Current-{}".format(gid)][0]
            dp = plot.plots["Original-{}".format(gid)][0]
        except KeyError:
            return

        if not self.xs.shape[0]:
            return

        ss = [
            p.plots[key][0]
            for p in graph.plots[1:]
            for key in p.plots
            if key.endswith("{}".format(gid))
        ]

        if sel is None and ss:
            sel = ss[0].index.metadata["selections"]

        if sel:
            self._set_renderer_selection(ss, sel)
        else:
            sel = []

        fxs = [a for i, a in enumerate(self.xs) if i not in sel]

        if fxs:
            fxes = [a for i, a in enumerate(self.xes) if i not in sel]
            xs, ys = self._calculate_probability_curve(fxs, fxes)
            wm, we, mswd, valid_mswd, n, pvalue = self._calculate_stats(xs, ys)
        else:
            n = 0
            ys = []
            xs = []
            wm, we, mswd, valid_mswd, pvalue = 0, 0, 0, False, 0

        lp.value.set_data(ys)
        lp.index.set_data(xs)

        opt = self.options
        for ov in lp.overlays:
            if isinstance(ov, MeanIndicatorOverlay):
                ov.set_x(wm)
                ov.error = we
                if ov.label:

                    mswd_args = None
                    if opt.display_mean_mswd:
                        mswd_args = (mswd, valid_mswd, n, pvalue)

                    text = self._make_mean_label(wm, we * opt.nsigma, n, mswd_args)
                    ov.label.text = text

        lp.overlays = [o for o in lp.overlays if not isinstance(o, PeakLabel)]

        self._add_peak_labels(lp, fxs)

        try:
            mi, ma = min(ys), max(ys)

            if sel:
                dp.visible = True
                xs, ys = self._calculate_probability_curve(self.xs, self.xes)
                dp.value.set_data(ys)
                dp.index.set_data(xs)
                mi, ma = min(mi, min(ys)), max(mi, max(ys))
            else:
                dp.visible = False

            self._set_y_limits(0, ma, min_=0)
        except ValueError:
            pass

        # graph.redraw()

    # ===============================================================================
    # utils
    # ===============================================================================
    def _make_mean_label(self, wm, we, n, mswd_args, **kw):
        text = self._build_label_text(
            wm,
            we,
            n,
            mswd_args=mswd_args,
            mswd_sig_figs=self.options.mswd_sig_figs,
            sig_figs=self.options.mean_sig_figs,
            percent_error=self.options.display_percent_error,
            display_n=self.options.display_mean_n,
            display_mswd_pvalue=self.options.display_mswd_pvalue,
            **kw
        )

        f = self.options.mean_label_format
        if f:
            ag = self.analysis_group
            ctx = {
                "identifier": ag.identifier,
                "sample": ag.sample,
                "material": ag.material,
            }

            tag = f.format(**ctx)
            text = "{} {}".format(tag, text)
        return text

    def _get_xs(self, key="age", nonsorted=False):
        xs = array([ai for ai in self._unpack_attr(key, nonsorted=nonsorted)])
        return xs

    def _add_aux_plot(
        self, ys, title, po, pid, gid=None, es=None, type="scatter", xs=None, **kw
    ):
        if gid is None:
            gid = self.group_id

        if xs is None:
            xs = self.xs

        plot = self.graph.plots[pid]
        if plot.value_scale == "log":
            ys = array(ys)
            ys[ys < 0] = 10 ** math.floor(math.log10(min(ys[ys > 0])))

        graph = self.graph

        plotkw = self.options.get_plot_dict(gid, 0)

        if "marker" not in plotkw:
            plotkw["marker"] = po.marker

        if "marker_size" not in plotkw:
            plotkw["marker_size"] = po.marker_size

        if "selection_marker_size" not in plotkw:
            plotkw["selection_marker_size"] = plotkw["marker_size"]

        if "type" in plotkw:
            plotkw.pop("type")

        kw.update(plotkw)
        s, p = graph.new_series(
            x=xs, y=ys, type=type, bind_id=self.group_id, plotid=pid, **kw
        )

        if self.options.show_correlation_ellipses and title == "K/Ca":
            o = CorrelationEllipsesOverlay(
                self.options._correlation_ellipses,
                self.options.get_colors(),
                component=s,
            )
            s.overlays.append(o)

        if es is not None:
            s.yerror = array(es)

        if not po.ytitle_visible:
            title = ""

        graph.set_y_title(title, plotid=pid)
        graph.set_series_label("{}-{}".format(title, self.group_id + 1), plotid=pid)
        s.history_id = self.group_id
        return s

    def _calculate_probability_curve(
        self, ages, errors, calculate_limits=False, limits=None
    ):
        xmi, xma = None, None
        if limits:
            xmi, xma = limits

        if not xmi and not xma:
            xmi, xma = self.graph.get_x_limits()
            if xmi == -Inf or xma == Inf:
                xmi, xma = self.xmi, self.xma

        opt = self.options

        if opt.probability_curve_kind == "kernel":
            return kernel_density(ages, errors, xmi, xma, n=N)

        else:
            if opt.use_asymptotic_limits and calculate_limits:

                def cfunc(x1, x2):
                    return cumulative_probability(ages, errors, x1, x2, n=N)

                bins, probs, x1, x2 = self._calculate_asymptotic_limits(
                    cfunc, tol=(opt.asymptotic_height_percent or 10)
                )
                self.trait_setq(xmi=x1, xma=x2)

                return bins, probs
            else:
                return cumulative_probability(ages, errors, xmi, xma, n=N)

    def _calculate_nominal_xlimits(self):
        return self.min_x(self.options.index_attr), self.max_x(self.options.index_attr)

    def _calculate_asymptotic_limits(self, cfunc, max_iter=200, tol=10):
        tol *= 0.01
        rx1, rx2 = None, None
        xs, ys = None, None
        xmi, xma = self._calculate_nominal_xlimits()
        x1, x2 = xmi, xma

        step_percent = 0.005
        step = step_percent * (xma - xmi)
        # aw = int(asymptotic_width * N * 0.01)
        for i in range(max_iter):
            if rx1 is None:
                x1 -= step
            else:
                x1 = rx1

            if rx2 is None:
                x2 += step
            else:
                x2 = rx2

            # grow step size
            step = step_percent * (x2 - x1)

            xs, ys = cfunc(x1, x2)
            tt = tol * ys.max()
            if rx1 is None:
                if ys[0] < tt:
                    rx1 = x1

            if rx2 is None:
                if ys[-1] < tt:
                    rx2 = x2

            if rx1 is not None and rx2 is not None:
                break

        if rx1 is None:
            rx1 = x1
        if rx2 is None:
            rx2 = x2

        return xs, ys, rx1, rx2

    def _calculate_asymptotic_limits2(
        self, cfunc, max_iter=200, asymptotic_width=10, tol=10
    ):
        """
        cfunc: callable that returns xs,ys and accepts xmin, xmax
                xs, ys= cfunc(x1,x2)

        asymptotic_width=percent of total width that is less than tol% of the total curve

        returns xs,ys,xmi,xma
        """
        tol *= 0.01
        rx1, rx2 = None, None
        xs, ys = None, None
        xmi, xma = self._calculate_nominal_xlimits()
        x1, x2 = xmi, xma
        step = 0.01 * (xma - xmi)
        aw = int(asymptotic_width * N * 0.01)
        for i in range(max_iter if aw else 1):
            x1 = xmi - step * i if rx1 is None else rx1
            x2 = xma + step * i if rx2 is None else rx2

            xs, ys = cfunc(x1, x2)

            low = ys[:aw]
            high = ys[-aw:]

            tt = tol * max(ys)

            if rx1 is None and (low < tt).all():
                rx1 = x1
            if rx2 is None and (high < tt).all():
                rx2 = x2
            if rx1 is not None and rx2 is not None:
                break

        # if tt is not None:
        # self.graph.add_horizontal_rule(tt)

        if rx1 is None:
            rx1 = x1
        if rx2 is None:
            rx2 = x2

        return xs, ys, rx1, rx2

    def _cmp_analyses(self, x):
        return x.age

    def _calculate_stats(self, xs, ys):
        ag = self.analysis_group
        options = self.options
        ag.attribute = options.index_attr
        ag.age_error_kind = options.error_calc_method
        ag.weighted_age_error_kind = options.error_calc_method
        ag.outlier_options = options.outlier_options
        ag.set_external_error(
            options.include_j_position_error,
            options.include_j_error_in_mean,
            options.include_decay_error,
            dirty=True,
        )

        mswd, valid_mswd, n, pvalue = self.analysis_group.get_mswd_tuple()
        mck = options.mean_calculation_kind
        if mck == KERNEL:
            wm, we = 0, 0
            peak_xs, peak_ys, xr = fast_find_peaks(ys, xs)
            wm = peak_xs[0]
            # wm = np_max(maxs, axis=1)[0]
        # elif mck == SCHAEN2020_1:
        #     wm, we, mswd, valid_mswd, n, pvalue = self.analysis_group.apply_outlier_filtering(SCHAEN2020_1)
        # elif mck == SCHAEN2020_2:
        #     wm, we, mswd, valid_mswd, n, pvalue = self.analysis_group.apply_outlier_filtering(SCHAEN2020_1)
        # elif mck == SCHAEN2020_3:
        #     wm, we, mswd, valid_mswd, n, pvalue = self.analysis_group.apply_outlier_filtering(SCHAEN2020_1)
        else:
            wage = self.analysis_group.weighted_age
            wm, we = nominal_value(wage), std_dev(wage)

        return wm, we, mswd, valid_mswd, n, pvalue


# ============= EOF =============================================
