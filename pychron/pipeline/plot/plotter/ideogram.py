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
from chaco.abstract_overlay import AbstractOverlay
from chaco.array_data_source import ArrayDataSource
from chaco.data_label import DataLabel
from chaco.scatterplot import render_markers
from enable.colors import ColorTrait
from pyface.message_dialog import warning
from traits.api import Array
# ============= standard library imports ========================
from numpy import array, arange, \
    Inf, argmax
from numpy import max as np_max
# ============= local library imports  ==========================
from uncertainties import nominal_value
from pychron.core.helpers.formatting import floatfmt
from pychron.core.stats.probability_curves import cumulative_probability, kernel_density
from pychron.pipeline.plot.flow_label import FlowPlotLabel

from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
# from pychron.pipeline.plot.overlays. import FlowPlotLabel
from pychron.pipeline.plot.overlays.ideogram_inset_overlay import IdeogramInset, IdeogramPointsInset

from pychron.pipeline.plot.overlays.mean_indicator_overlay import MeanIndicatorOverlay
from pychron.core.stats.peak_detection import find_peaks, find_fine_peak
# from pychron.pipeline.plot import OverlayMoveTool
from pychron.pipeline.plot.point_move_tool import OverlayMoveTool
from pychron.pipeline.plot.ticks import IntTickGenerator
from pychron.pychron_constants import PLUSMINUS, SIGMA

N = 500


class PeakLabel(DataLabel):
    pass


class LatestOverlay(AbstractOverlay):
    data_position = None
    color = ColorTrait('transparent')

    # The color of the outline to draw around the marker.
    outline_color = ColorTrait('orange')

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            pts = self.component.map_screen(self.data_position)
            render_markers(gc, pts, 'circle', 5, self.color_, 2, self.outline_color_)


class Ideogram(BaseArArFigure):
    xs = Array
    xes = Array
    # index_key = 'uage'
    ytitle = 'Relative Probability'
    # _reverse_sorted_analyses = True
    # _analysis_number_cnt = 1

    # x_grid_visible = False
    # y_grid_visible = False

    _omit_key = 'omit_ideo'

    # def get_update_dict(self):
    #     return {'_analysis_number_cnt': self._analysis_number_cnt}

    def plot(self, plots, legend=None):
        """
            plot data on plots
        """
        opt = self.options
        if opt.index_attr:
            index_attr = opt.index_attr
            if index_attr == 'uage' and opt.include_j_error:
                index_attr = 'uage_w_j_err'
        else:
            warning(None, 'X Value not set. Defaulting to Age')
            index_attr = 'uage'

        graph = self.graph

        try:
            self.xs, self.xes = array([(ai.nominal_value, ai.std_dev)
                                       for ai in self._get_xs(key=index_attr)]).T

        except (ValueError, AttributeError), e:
            print 'asdfasdf', e, index_attr
            return

        # omit = self._get_omitted(self.sorted_analyses)
        # omit = set(omit)
        selection = self._get_omitted_by_tag(self.sorted_analyses)
        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            try:
                args = getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)
            except AttributeError:
                import traceback

                traceback.print_exc()
                continue

            if args:
                scatter, aux_selection, invalid = args
                selection.extend(aux_selection)
                # print omit, selection, invalid
                # omit = omit.union(set(selection))

                # self.update_options_limits(pid)

                # for i, ai in enumerate(self.sorted_analyses):
                #     # print ai.record_id, i in omit
                #     ai.value_filter_omit = i in omit

                # self._asymptotic_limit_flag = True
                # opt = self.options
                # xmi, xma = self.xmi, self.xma
                # pad = '0.05'

                # if opt.use_asymptotic_limits:
                # xmi, xma = self.xmi, self.xma
                # elif opt.use_centered_range:
                # w2 = opt.centered_range / 2.0
                # r = self.center
                # xmi, xma = r - w2, w2 + r
                # pad=False
                # elif opt.xlow or opt.xhigh:
                # xmi, xma = opt.xlow, opt.xhigh
                # pad=False

        # print opt.use_centered_range, self.center, xmi, xma

        # self.xmi = min(xmi, self.xmi)
        # self.xma = max(xma, self.xma)
        # graph.set_x_limits(min_=xmi, max_=xma,pad=pad)

        t = index_attr
        if index_attr == 'uF':
            t = 'Ar40*/Ar39k'
        elif index_attr in ('uage', 'uage_w_j_err'):
            ref = self.analyses[0]
            age_units = ref.arar_constants.age_units
            t = 'Age ({})'.format(age_units)

        graph.set_x_title(t, plotid=0)

        # turn off ticks for prob plot by default
        plot = graph.plots[0]
        plot.value_axis.tick_label_formatter = lambda x: ''
        plot.value_axis.tick_visible = False

        if selection:
            print 'selection {}'.format(selection)
            self._rebuild_ideo(selection)

            # if omit:
            #     self._rebuild_ideo(list(omit))

    def mean_x(self, attr):
        # todo: handle other attributes
        return self.analysis_group.weighted_age.nominal_value

        # try:
        # return max([ai
        # for ai in self._unpack_attr(attr)])
        # except (AttributeError, ValueError):
        # return 0

    def max_x(self, attr):
        try:
            return max([ai.nominal_value + ai.std_dev
                        for ai in self._unpack_attr(attr) if ai is not None])
        except (AttributeError, ValueError), e:
            print 'max', e, 'attr={}'.format(attr)
            return 0

    def min_x(self, attr):
        try:
            return min([ai.nominal_value - ai.std_dev
                        for ai in self._unpack_attr(attr) if ai is not None])
        except (AttributeError, ValueError), e:
            print 'min', e
            return 0

    # ===============================================================================
    # plotters
    # ===============================================================================
    def _plot_aux(self, title, vk, ys, po, plot, pid,
                  es=None):

        # omits = self._get_aux_plot_omits(po, ys, es)
        # print 'plot aux {}'.format(omits)
        selection = []
        invalid = []

        scatter = self._add_aux_plot(ys,
                                     title, po, pid)

        nsigma = self.options.error_bar_nsigma

        self._add_error_bars(scatter, self.xes, 'x', nsigma,
                             end_caps=self.options.x_end_caps,
                             visible=po.x_error)
        if es:
            self._add_error_bars(scatter, es, 'y', nsigma,
                                 end_caps=self.options.y_end_caps,
                                 visible=po.y_error)

        if po.show_labels:
            self._add_point_labels(scatter)

        func = self._get_index_attr_label_func()
        self._add_scatter_inspector(scatter,
                                    additional_info=func)

        return scatter, selection, invalid

    def _plot_analysis_number(self, *args, **kw):
        return self.__plot_analysis_number(*args, **kw)

    def _plot_analysis_number_nonsorted(self, *args, **kw):
        kw['nonsorted'] = True
        return self.__plot_analysis_number(*args, **kw)

    def _get_nonsorted_xs(self):
        opt = self.options
        if opt.index_attr:
            index_attr = opt.index_attr
            if index_attr == 'uage' and opt.include_j_error:
                index_attr = 'uage_w_j_err'

        return [v for v in self._unpack_attr()]

    def __plot_analysis_number(self, po, plot, pid, nonsorted=False):
        xs = self.xs
        xes = self.xes
        n = xs.shape[0]

        startidx = 1
        # name = 'analysis #'
        items = self.sorted_analyses
        if nonsorted:
            # items = self.analyses
            name = 'A# Nonsorted'
            tag = 'Analysis Number Nonsorted'
            opt = self.options

            index_attr = opt.index_attr
            if index_attr == 'uage' and opt.include_j_error:
                index_attr = 'uage_w_j_err'

            xs = [nominal_value(x) for x in self._get_xs(key=index_attr, nonsorted=True)]
        else:
            name = 'Analysis #'
            tag = 'Analysis Number'
            xs = self.xs

        for p in self.graph.plots:
            # if title is not visible title=='' so check tag instead

            if p.y_axis.tag == tag:
                for k, rend in p.plots.iteritems():
                    # if title is not visible k == e.g '-1' instead of 'Analysis #-1'
                    if k.startswith(name) or k.startswith('-'):
                        startidx += rend[0].index.get_size()

        if self.options.analysis_number_sorting == 'Oldest @Top' or nonsorted:
            ys = arange(startidx, startidx + n)
        else:
            ys = arange(startidx + n - 1, startidx - 1, -1)

        if self.options.use_cmap_analysis_number:
            ans = self.sorted_analyses
            ts = array([ai.timestamp for ai in ans])
            ts -= ts[0]
            scatter = self._add_aux_plot(xs, ys, name, po, pid,
                                         colors=ts,
                                         color_map_name=self.options.cmap_analysis_number,
                                         type='cmap_scatter',
                                         xs=xs)
        else:
            if nonsorted:
                data = sorted(zip(xs, ys), key=lambda x: x[0])
                xs, ys = zip(*data)

            scatter = self._add_aux_plot(ys, name, po, pid, xs=xs)

        if self.options.use_latest_overlay:
            idx = argmax(ts)
            dx = scatter.index.get_data()[idx]
            dy = scatter.value.get_data()[idx]

            scatter.overlays.append(LatestOverlay(component=scatter,
                                                  data_position=array([(dx, dy)])))

        self._add_error_bars(scatter, xes, 'x', self.options.error_bar_nsigma,
                             end_caps=self.options.x_end_caps,
                             visible=po.x_error)

        if po.show_labels:
            self._add_point_labels(scatter)

        # set tick generator
        gen = IntTickGenerator()
        plot.y_axis.tick_generator = gen
        plot.y_grid.tick_generator = gen

        my = max(ys) + 1
        plot.value_range.tight_bounds = True
        self._set_y_limits(0, my, min_=0, max_=my, pid=pid)

        # print 'setting ylimits {}'.format(my)
        omits, invalids, outliers = self._do_aux_plot_filtering(scatter, po, xs, xes)
        func = self._get_index_attr_label_func()
        self._add_scatter_inspector(scatter,
                                    items=items,
                                    value_format=lambda x: '{:d}'.format(int(x)),
                                    additional_info=func)

        selection = omits + outliers

        return scatter, selection, invalids

    def _get_index_attr_label_func(self):
        ia = self.options.index_attr
        if ia.startswith('uage'):
            name = 'Age'
            ia = 'uage'
            if self.options.include_j_error:
                ia = 'uage_w_j_err'
        else:
            name = ia

        f = lambda i, x, y, ai: u'{}= {}'.format(name, ai.value_string(ia))
        return f

    def _plot_relative_probability(self, po, plot, pid):
        graph = self.graph
        bins, probs = self._calculate_probability_curve(self.xs, self.xes, calculate_limits=True)

        ogid = self.group_id
        gid = ogid + 1
        sgid = ogid * 2

        plotkw = self.options.get_plot_dict(ogid)

        line, _ = graph.new_series(x=bins, y=probs, plotid=pid, **plotkw)

        if self.options.label_all_peaks:
            self._add_peak_labels(line, self.xs, self.xes)

        graph.set_series_label('Current-{}'.format(gid), series=sgid, plotid=pid)

        # add the dashed original line
        graph.new_series(x=bins, y=probs,
                         plotid=pid,
                         visible=False,
                         color=line.color,
                         line_style='dash')

        graph.set_series_label('Original-{}'.format(gid), series=sgid + 1, plotid=pid)

        self._add_info(graph, plot)
        self._add_mean_indicator(graph, line, po, bins, probs, pid)

        mi, ma = min(probs), max(probs)

        # if not po.has_ylimits():
        self._set_y_limits(mi, ma, min_=0, pad='0.025')

        d = lambda a, b, c, d: self.update_index_mapper(a, b, c, d)
        plot.index_mapper.on_trait_change(d, 'updated')

        if self.options.display_inset:
            xs = self.xs
            n = xs.shape[0]

            startidx = 1
            if self.group_id > 0:
                for ov in plot.overlays:
                    if isinstance(ov, IdeogramPointsInset):
                        print self.group_id, startidx, ov.value.get_bounds()[1] + 1
                        startidx = max(startidx, ov.value.get_bounds()[1] + 1)
            else:
                startidx = 1

            if self.options.analysis_number_sorting == 'Oldest @Top':
                ys = arange(startidx, startidx + n)
            else:
                ys = arange(startidx + n - 1, startidx - 1, -1)

            yma2 = max(ys) + 1
            h = self.options.inset_height / 2.0
            if self.group_id == 0:
                # bgcolor = self.options.get_formatting_value('plot_bgcolor')
                bgcolor = self.options.plot_bgcolor
            else:
                bgcolor = 'transparent'

            d = self.options.get_plot_dict(ogid)
            o = IdeogramPointsInset(self.xs, ys,
                                    color=d['color'],
                                    outline_color=d['color'],
                                    bgcolor=bgcolor,
                                    width=self.options.inset_width,
                                    height=h,
                                    visible_axes=False,
                                    xerror=ArrayDataSource(self.xes),
                                    location=self.options.inset_location)
            # o.x_axis.visible = False
            plot.overlays.append(o)

            cfunc = lambda x1, x2: cumulative_probability(self.xs, self.xes, x1, x2, n=N)
            xs, ys, xmi, xma = self._calculate_asymptotic_limits(cfunc,
                                                                 # asymptotic_width=10,
                                                                 tol=self.options.asymptotic_height_percent)
            oo = IdeogramInset(xs, ys,
                               color=d['color'],
                               bgcolor=bgcolor,
                               yoffset=h,
                               visible_axes=self.group_id == 0,
                               width=self.options.inset_width,
                               height=self.options.inset_height,
                               location=self.options.inset_location)

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

    def _add_peak_labels(self, line, ages, errors):
        xs = line.index.get_data()
        ys = line.value.get_data()

        try:
            maxp, minp = find_peaks(ys, xs, lookahead=1)
        except IndexError:
            return

        for age, relative_prob in maxp:
            func = lambda mi, ma: cumulative_probability(ages, errors, mi, ma, n=N)
            limits = (age * 0.99, age * 1.01)
            try:
                p = find_fine_peak(func=func, initial_limits=limits, tol=0.001, lookahead=1)
            except IndexError:
                continue

            label = PeakLabel(line,
                              data_point=(p, relative_prob),
                              label_text=floatfmt(p, n=3),
                              border_visible=False,
                              marker_visible=False,
                              show_label_coords=False)
            line.overlays.append(label)

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = []
                if self.options.show_mean_info:
                    m = self.options.mean_calculation_kind
                    s = self.options.nsigma
                    es = self.options.error_bar_nsigma
                    ts.append(u'Mean: {} {}{}{} Data: {}{}{}'.format(m, PLUSMINUS, s, SIGMA, PLUSMINUS, es, SIGMA))
                if self.options.show_error_type_info:
                    ts.append('Error Type: {}'.format(self.options.error_calc_method))

                if ts:
                    # font = self.options.get_formatting_value('label_font', 'error_info_font')
                    pl = FlowPlotLabel(text='\n'.join(ts),
                                       overlay_position='inside top',
                                       hjustify='left',
                                       font=self.options.error_info_font,
                                       component=plot)
                    plot.overlays.append(pl)

    def _add_mean_indicator(self, g, line, po, bins, probs, pid):
        wm, we, mswd, valid_mswd = self._calculate_stats(bins, probs)
        # print wm, we
        ogid = self.group_id
        gid = ogid + 1

        text = ''
        if self.options.display_mean:
            n = self.xs.shape[0]
            mswd_args = (mswd, valid_mswd, n)
            text = self._build_label_text(wm, we, n,
                                          mswd_args=mswd_args,
                                          sig_figs=self.options.mean_sig_figs,
                                          percent_error=self.options.display_percent_error)

        group = self.options.get_group(self.group_id)
        color = group.color

        m = MeanIndicatorOverlay(component=line,
                                 x=wm,
                                 y=20 * gid,
                                 error=we,
                                 nsgima=self.options.nsigma,
                                 color=color,
                                 visible=self.options.display_mean_indicator,
                                 id='mean_{}'.format(self.group_id))

        # font = self.options.get_formatting_value('label_font', 'mean_indicator_font')
        font = self.options.mean_indicator_font
        m.font = str(font).lower()
        m.text = text

        # print m.label.font
        line.overlays.append(m)

        line.tools.append(OverlayMoveTool(component=m,
                                          constrain='x'))

        m.on_trait_change(self._handle_overlay_move, 'altered_screen_point')

        if m.id in po.overlay_positions:
            ap = po.overlay_positions[m.id]
            m.y = ap[1]

        if m.label:
            m.label.on_trait_change(self._handle_label_move, 'altered_screen_point')
            if m.label.id in po.overlay_positions:
                ap = po.overlay_positions[m.label.id]
                m.label.altered_screen_point = (ap[0], ap[1])
                m.label.trait_set(x=ap[0], y=ap[1])

        return m

    def update_index_mapper(self, obj, name, old, new):
        if new:
            self.update_graph_metadata(None, name, old, new)

    def update_graph_metadata(self, obj, name, old, new):
        # print obj, name, old,new
        sorted_ans = self.sorted_analyses
        if obj:
            # hover = obj.metadata.get('hover')
            # if hover:
            #     hoverid = hover[0]
            # try:
            # self.selected_analysis = sorted_ans[hoverid]
            #
            # except IndexError, e:
            # print 'asaaaaa', e
            #     return
            # else:
            # self.selected_analysis = None

            self._filter_metadata_changes(obj, sorted_ans, self._rebuild_ideo)
            # self._set_selected(sorted_ans, sel)
            # set the temp_status for all the analyses
            # for i, a in enumerate(sorted_ans):
            # a.temp_status = 1 if i in sel else 0
            # else:
            # sel = [i for i, a in enumerate(sorted_ans)
            # if a.temp_status]
            # sel = self._get_omitted(sorted_ans)
            # print 'update graph meta'
            # self._rebuild_ideo(sel)

    def _rebuild_ideo(self, sel):
        print 'rebuild ideo {}'.format(sel)
        graph = self.graph

        if len(graph.plots) > 1:
            ss = [p.plots[key][0]
                  for p in graph.plots[1:]
                  for key in p.plots
                  if key.endswith('{}'.format(self.group_id + 1))]
            # print ss, sel
            self._set_renderer_selection(ss, sel)

        plot = graph.plots[0]
        gid = self.group_id + 1
        lp = plot.plots['Current-{}'.format(gid)][0]
        dp = plot.plots['Original-{}'.format(gid)][0]
        # sp = plot.plots['Mean-{}'.format(gid)][0]

        def f(a):
            i, _ = a
            # print a, i not in sel, sel
            return i not in sel

        # d = zip(self.xs, self.xes)
        # oxs, oxes = zip(*d)
        # d = filter(f, enumerate(d))
        if not self.xs.shape[0]:
            return

        _, fxs = zip(*filter(f, enumerate(self.xs)))
        _, fxes = zip(*filter(f, enumerate(self.xes)))
        n = len(fxs)
        if n:
            # fxs, fxes = zip(*[(a, b) for _, (a, b) in d])

            xs, ys = self._calculate_probability_curve(fxs, fxes)
            wm, we, mswd, valid_mswd = self._calculate_stats(xs, ys)

            lp.value.set_data(ys)
            lp.index.set_data(xs)

            # n = len(fxs)
            total_n = self.xs.shape[0]
            for ov in lp.overlays:
                if isinstance(ov, MeanIndicatorOverlay):
                    ov.set_x(wm)
                    # ov.x=wm
                    ov.error = we
                    if ov.label:
                        mswd_args = mswd, valid_mswd, n
                        ov.label.text = self._build_label_text(wm, we, n,
                                                               mswd_args=mswd_args,
                                                               total_n=total_n,
                                                               percent_error=self.options.display_percent_error,
                                                               sig_figs=self.options.mean_sig_figs)

            lp.overlays = [o for o in lp.overlays if not isinstance(o, PeakLabel)]

            self._add_peak_labels(lp, fxs, fxes)

            # update the data label position
            # for ov in sp.overlays:
            # if isinstance(ov, DataLabel):
            # _, y = ov.data_point
            # ov.data_point = wm, y
            # n = len(fxs)
            # ov.label_text = self._build_label_text(wm, we, mswd, valid_mswd, n)

            if sel:
                dp.visible = True
                # xs, ys = self._calculate_probability_curve(oxs, oxes)
                # dp.value.set_data(ys)
                # dp.index.set_data(xs)
            else:
                dp.visible = False
        graph.redraw()
        # ===============================================================================
        # utils
        # ===============================================================================

    def _get_xs(self, key='age', nonsorted=False):
        xs = array([ai for ai in self._unpack_attr(key, nonsorted=nonsorted)])
        # xs = array(self._unpack_attr(key, nonsorted=nonsorted))
        return xs

    def _add_aux_plot(self, ys, title, po, pid, type='scatter', xs=None, **kw):
        if xs is None:
            xs = self.xs

        plot = self.graph.plots[pid]
        if plot.value_scale == 'log':
            ys = array(ys)
            ys[ys < 0] = 1e-20

        graph = self.graph

        group = self.options.get_group(self.group_id)
        color = group.color

        # print 'aux plot',title, self.group_id
        s, p = graph.new_series(
            x=xs, y=ys,
            color=color,
            type=type,
            marker=po.marker,
            marker_size=po.marker_size,
            selection_marker_size=po.marker_size,
            bind_id=self.group_id,
            plotid=pid, **kw)

        if not po.ytitle_visible:
            title = ''

        if '<sup>' in title or '<sub>' in title:
            self._set_ml_title(title, pid, 'y')
        else:
            graph.set_y_title(title, plotid=pid)
        # graph.set_y_title(title, plotid=pid)
        graph.set_series_label('{}-{}'.format(title, self.group_id + 1),
                               plotid=pid)
        return s

    def _calculate_probability_curve(self, ages, errors, calculate_limits=False, limits=None):
        xmi, xma = None, None
        if limits:
            xmi, xma = limits

        if not xmi and not xma:
            xmi, xma = self.graph.get_x_limits()
            if xmi == -Inf or xma == Inf:
                xmi, xma = self.xmi, self.xma

        opt = self.options

        if opt.probability_curve_kind == 'kernel':
            return kernel_density(ages, errors, xmi, xma, n=N)

        else:
            if opt.use_asymptotic_limits and calculate_limits:
                cfunc = lambda x1, x2: cumulative_probability(ages, errors, x1, x2, n=N)
                # bins,probs=cfunc(xmi,xma)
                # wa = self.analysis_group.weighted_age
                # m, e = nominal_value(wa), std_dev(wa)
                # xmi, xma = m - e, m + e
                bins, probs, x1, x2 = self._calculate_asymptotic_limits(cfunc,
                                                                        tol=(opt.asymptotic_height_percent or 10))
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
        for i in xrange(max_iter):
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
            # print i, x1, x2, tt, tol, ys.max(), ys[0], ys[-1]
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

        # print 'set limits to {},{}'.format(rx1, rx2)
        return xs, ys, rx1, rx2

    def _calculate_asymptotic_limits2(self, cfunc, max_iter=200, asymptotic_width=10,
                                      tol=10):
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
        for i in xrange(max_iter if aw else 1):
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
        ag.attribute = self.options.index_attr
        ag.weighted_age_error_kind = self.options.error_calc_method
        ag.include_j_error_in_mean = self.options.include_j_error_in_mean
        ag.include_j_error_in_individual_analyses = self.options.include_j_error

        mswd, valid_mswd, n = self.analysis_group.get_mswd_tuple()

        if self.options.mean_calculation_kind == 'kernel':
            wm, we = 0, 0
            delta = 1
            maxs, _mins = find_peaks(ys, xs, delta=delta, lookahead=1)
            wm = np_max(maxs, axis=1)[0]
        else:
            wage = self.analysis_group.weighted_age
            wm, we = wage.nominal_value, wage.std_dev

        return wm, we, mswd, valid_mswd

        # def _calc_error(self, we, mswd):
        # ec = self.options.error_calc_method
        # n = self.options.nsigma
        # if ec == 'SEM':
        # a = 1
        # elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
        # a = 1
        # if mswd > 1:
        # a = mswd ** 0.5
        # return we * a * n

# ============= EOF =============================================
