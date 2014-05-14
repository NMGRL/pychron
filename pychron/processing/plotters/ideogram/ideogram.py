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
from traits.api import Float, Array
#============= standard library imports ========================
from numpy import linspace, pi, exp, zeros, ones, array, arange, \
    Inf
from numpy import max as np_max
#============= local library imports  ==========================

from pychron.processing.plotters.arar_figure import BaseArArFigure
from pychron.processing.plotters.flow_label import FlowPlotLabel
from pychron.processing.plotters.ideogram.ideogram_inset_overlay import IdeogramInset

from pychron.processing.plotters.ideogram.mean_indicator_overlay import MeanIndicatorOverlay
from pychron.core.stats.peak_detection import find_peaks
from pychron.processing.plotters.point_move_tool import OverlayMoveTool

N = 500


class Ideogram(BaseArArFigure):
    xmi = Float
    xma = Float
    xs = Array
    xes = Array
    # index_key = 'uage'
    ytitle = 'Relative Probability'
    #     _reverse_sorted_analyses = True
    _analysis_number_cnt = 0

    x_grid_visible = False
    y_grid_visible = False

    _omit_key = 'omit_ideo'

    def plot(self, plots):
        """
            plot data on plots
        """
        opt = self.options
        index_attr = 'uage'
        if opt.index_attr:
            index_attr = opt.index_attr
            if not opt.include_j_error:
                index_attr = 'uage_wo_j_err'

        graph = self.graph

        self._analysis_number_cnt = 0
        try:
            self.xs, self.xes = array([(ai.nominal_value, ai.std_dev)
                                       for ai in self._get_xs(key=index_attr)]).T
        except (ValueError, AttributeError), e:
            print 'asdfasdf', e
            return

        omit = self._get_omitted(self.sorted_analyses,
                                 omit='omit_ideo',
                                 include_value_filtered=False)
        omit = set(omit)
        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            try:
                args = getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)
            except AttributeError:
                import traceback

                traceback.print_exc()
                continue

            if args:
                scatter, omits = args
                omit = omit.union(set(omits))

                # self.update_options_limits(pid)

        for i, ai in enumerate(self.sorted_analyses):
            # print ai.record_id, i in omit
            ai.value_filter_omit = i in omit

            # self._asymptotic_limit_flag = True
            # opt = self.options
            # xmi, xma = self.xmi, self.xma
            # pad = '0.05'


            # if opt.use_asymptotic_limits:
            #     xmi, xma = self.xmi, self.xma
            # elif opt.use_centered_range:
            #     w2 = opt.centered_range / 2.0
            #     r = self.center
            #     xmi, xma = r - w2, w2 + r
            # pad=False
            # elif opt.xlow or opt.xhigh:
            #     xmi, xma = opt.xlow, opt.xhigh
            # pad=False

        # print opt.use_centered_range, self.center, xmi, xma

        # self.xmi = min(xmi, self.xmi)
        # self.xma = max(xma, self.xma)
        # graph.set_x_limits(min_=xmi, max_=xma,pad=pad)

        t = index_attr
        if index_attr == 'uF':
            t = 'Ar40*/Ar39k'
        elif index_attr in ('uage', 'uage_wo_j_err'):
            ref = self.analyses[0]
            age_units = ref.arar_constants.age_units
            t = 'Age ({})'.format(age_units)

        graph.set_x_title(t)

        #turn off ticks for prob plot by default
        plot = graph.plots[0]
        plot.value_axis.tick_label_formatter = lambda x: ''
        plot.value_axis.tick_visible = False

        #print 'ideo omit', self.group_id, omit
        if omit:
            self._rebuild_ideo(list(omit))

    def mean_x(self, attr):
        #todo: handle other attributes
        return self.analysis_group.weighted_age.nominal_value

        # try:
        #     return max([ai
        #                 for ai in self._unpack_attr(attr)])
        # except (AttributeError, ValueError):
        #     return 0

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

    #===============================================================================
    # plotters
    #===============================================================================
    def _plot_aux(self, title, vk, ys, po, plot, pid,
                  es=None):

        omits = self._get_aux_plot_omits(po, ys)

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

        ia = 'uage_wo_j_err'
        if self.options.include_j_error:
            ia = 'uage'

        f = lambda x: u'Age= {}'.format(x.value_string(ia))
        self._add_scatter_inspector(scatter,
                                    additional_info=f)

        return scatter, omits

    def _plot_analysis_number(self, *args, **kw):
        return self.__plot_analysis_number(*args, **kw)

    def _plot_analysis_number_stacked(self, *args, **kw):
        kw['stacked'] = True
        return self.__plot_analysis_number(*args, **kw)

    def __plot_analysis_number(self, po, plot, pid, stacked=False):
        xs = self.xs
        n = xs.shape[0]

        startidx = 1
        name = 'analysis #'
        if stacked:
            name = 'Analysis #'
            for p in self.graph.plots:

                #if title is not visible title=='' so check tag instead
                if p.y_axis.tag == 'Analysis Number Stacked':
                    for k, rend in p.plots.iteritems():
                        #if title is not visible k == e.g '-1' instead of 'Analysis #-1'
                        if k.startswith(name) or k.startswith('-'):
                            startidx += rend[0].index.get_size()

        if self.options.analysis_number_sorting == 'Oldest @Top':
            ys = arange(startidx, startidx + n)
        else:
            ys = arange(startidx + n - 1, startidx - 1, -1)
        scatter = self._add_aux_plot(ys, name, po, pid)

        self._add_error_bars(scatter, self.xes, 'x', self.options.error_bar_nsigma,
                             end_caps=self.options.x_end_caps,
                             visible=po.x_error)

        if po.show_labels:
            self._add_point_labels(scatter)

        my = max(ys) + 1
        # if not po.has_ylimits():
        #     self._set_y_limits(0, my, pid=pid)
        # else:
        plot.value_range.tight_bounds = True
        # ly, uh = po.ylimits
        # if uh < my:
        self._set_y_limits(0, my, min_=0, pid=pid)

        omits = self._get_aux_plot_omits(po, ys)
        ia = self.options.index_attr

        f = lambda x: u'Age= {}'.format(x.value_string(ia))

        self._add_scatter_inspector(scatter,
                                    value_format=lambda x: '{:d}'.format(int(x)),
                                    additional_info=f)

        return scatter, omits

    def _plot_relative_probability(self, po, plot, pid):
        graph = self.graph

        bins, probs = self._calculate_probability_curve(self.xs, self.xes, calculate_limits=True)

        ogid = self.group_id
        gid = ogid + 1
        sgid = ogid * 2
        # print 'ogid={} gid={} sgid={}'.format(ogid, gid, sgid)
        plotkw = dict()
        # if self.group_id==0:
        # if self.options.use_filled_line:
        plotkw.update(**self.options.get_fill_dict(ogid))
        # color= self.options.fill_color
        # color.setAlphaF(self.options.fill_alpha*0.01)
        # plotkw['fill_color']=self.options.fill_color
        # plotkw['type']='filled_line'
        # else:

        line, _ = graph.new_series(x=bins, y=probs, plotid=pid, **plotkw)

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

        if self.group_id == 0:
            if self.options.display_inset:
                cfunc = lambda x1, x2: self._cumulative_probability(self.xs, self.xes, x1, x2)
                xs, ys, xmi, xma = self._calculate_asymptotic_limits(cfunc,
                                                                     asymptotic_width=10,
                                                                     tol=10)
                plot.overlays.append(IdeogramInset(xs, ys,
                                                   width=self.options.inset_width,
                                                   height=self.options.inset_height,
                                                   location=self.options.inset_location))


                #===============================================================================
                # overlays
                #===============================================================================
                #def _add_limits_tool(self, plot):

                #t = LimitsTool(component=plot)
                #o = LimitOverlay(component=plot, tool=t)
                #plot.tools.append(t)
                #plot.overlays.append(o)

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = []
                if self.options.show_mean_info:
                    m = self.options.mean_calculation_kind
                    s = self.options.nsigma
                    es = self.options.error_bar_nsigma
                    ts.append('Mean: {} +/-{}s Data: +/-{}s'.format(m, s, es))
                if self.options.show_error_type_info:
                    ts.append('Error Type:{}'.format(self.options.error_calc_method))

                if ts:
                    pl = FlowPlotLabel(text='\n'.join(ts),
                                       overlay_position='inside top',
                                       hjustify='left',
                                       font=self.options.error_info_font,
                                       component=plot)
                    plot.overlays.append(pl)

    def _add_mean_indicator(self, g, line, po, bins, probs, pid):
        # maxp = max(probs)
        wm, we, mswd, valid_mswd = self._calculate_stats(bins, probs)

        #ym = maxp * percentH + offset
        #set ym in screen space
        #convert to data space
        ogid = self.group_id
        gid = ogid + 1
        # sgid = ogid * 2

        text = ''
        if self.options.display_mean:
            text = self._build_label_text(wm, we, mswd, valid_mswd, len(self.xs),
                                          value_sig_figs=self.options.mean_sig_figs,
                                          error_sig_figs=self.options.mean_error_sig_figs,
                                          percent_error=self.options.display_percent_error)

        m = MeanIndicatorOverlay(component=line,
                                 x=wm,
                                 y=20 * gid,
                                 error=we,
                                 nsgima=self.options.nsigma,
                                 color=line.color,
                                 visible=self.options.display_mean_indicator,
                                 id='mean_{}'.format(self.group_id))

        m.font = self.options.mean_indicator_font
        m.text = text
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
        #print obj, name, old,new
        sorted_ans = self.sorted_analyses
        if obj:
            hover = obj.metadata.get('hover')
            if hover:
                hoverid = hover[0]
                try:
                    self.selected_analysis = sorted_ans[hoverid]

                except IndexError, e:
                    print 'asaaaaa', e
                    return
            else:
                self.selected_analysis = None

            sel = self._filter_metadata_changes(obj, self._rebuild_ideo, sorted_ans)
            #self._set_selected(sorted_ans, sel)
            # set the temp_status for all the analyses
            #for i, a in enumerate(sorted_ans):
            #    a.temp_status = 1 if i in sel else 0
        else:
            #sel = [i for i, a in enumerate(sorted_ans)
            #            if a.temp_status]
            sel = self._get_omitted(sorted_ans, omit='omit_ideo')
            #print 'update graph meta'
            self._rebuild_ideo(sel)

    def _rebuild_ideo(self, sel):
        #print 'rebuild ideo {}'.format(sel)
        graph = self.graph

        if len(graph.plots) > 1:
            ss = [p.plots[key][0]
                  for p in graph.plots[1:]
                  for key in p.plots
                  if key.endswith('{}'.format(self.group_id + 1))]
            #print ss, sel
            self._set_renderer_selection(ss, sel)

        plot = graph.plots[0]
        gid = self.group_id + 1
        lp = plot.plots['Current-{}'.format(gid)][0]
        dp = plot.plots['Original-{}'.format(gid)][0]
        #sp = plot.plots['Mean-{}'.format(gid)][0]

        def f(a):
            i, _ = a
            #print a, i not in sel, sel
            return i not in sel

        d = zip(self.xs, self.xes)
        oxs, oxes = zip(*d)
        d = filter(f, enumerate(d))
        if d:
            fxs, fxes = zip(*[(a, b) for _, (a, b) in d])

            xs, ys = self._calculate_probability_curve(fxs, fxes)
            wm, we, mswd, valid_mswd = self._calculate_stats(xs, ys)

            lp.value.set_data(ys)
            lp.index.set_data(xs)

            #sp.index.set_data([wm])
            #sp.xerror.set_data([we])

            mi = min(ys)
            ma = max(ys)
            self._set_y_limits(mi, ma, min_=0)

            n = len(fxs)
            for ov in lp.overlays:
                if isinstance(ov, MeanIndicatorOverlay):
                    ov.set_x(wm)
                    #ov.x=wm
                    ov.error = we
                    if ov.label:
                        ov.label.text = self._build_label_text(wm, we, mswd, valid_mswd, n,
                                                               percent_error=self.options.display_percent_error,
                                                               value_sig_figs=self.options.mean_sig_figs,
                                                               error_sig_figs=self.options.mean_error_sig_figs)

            # update the data label position
            #for ov in sp.overlays:
            #    if isinstance(ov, DataLabel):
            #        _, y = ov.data_point
            #        ov.data_point = wm, y
            #        n = len(fxs)
            #        ov.label_text = self._build_label_text(wm, we, mswd, valid_mswd, n)

            if sel:
                dp.visible = True
                xs, ys = self._calculate_probability_curve(oxs, oxes)
                dp.value.set_data(ys)
                dp.index.set_data(xs)
            else:
                dp.visible = False
        graph.redraw()
        #===============================================================================
        # utils
        #===============================================================================

    def _get_xs(self, key='age'):
        xs = array([ai for ai in self._unpack_attr(key)])
        return xs

    def _add_aux_plot(self, ys, title, po, pid, **kw):
        plot = self.graph.plots[pid]
        if plot.value_scale == 'log':
            ys = array(ys)
            ys[ys < 0] = 1e-20

        graph = self.graph

        #print 'aux plot',title, self.group_id
        s, p = graph.new_series(
            x=self.xs, y=ys,
            type='scatter',
            marker='circle',
            marker_size=3,
            selection_marker_size=3,
            bind_id=self.group_id,
            plotid=pid, **kw)

        if not po.ytitle_visible:
            title = ''

        graph.set_y_title(title,
                          plotid=pid)

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
            return self._kernel_density(ages, errors, xmi, xma)

        else:
            if opt.use_asymptotic_limits and calculate_limits:
                cfunc = lambda x1, x2: self._cumulative_probability(ages, errors, x1, x2)
                # bins,probs=cfunc(xmi,xma)
                # wa = self.analysis_group.weighted_age
                # m, e = nominal_value(wa), std_dev(wa)
                # xmi, xma = m - e, m + e
                bins, probs, x1, x2 = self._calculate_asymptotic_limits(cfunc,
                                                                        asymptotic_width=(opt.asymptotic_width or 10),
                                                                        tol=(opt.asymptotic_percent or 10))
                self.trait_setq(xmi=x1, xma=x2)

                return bins, probs
            else:
                return self._cumulative_probability(ages, errors, xmi, xma)

    def _kernel_density(self, ages, errors, xmi, xma):
        from scipy.stats.kde import gaussian_kde

        pdf = gaussian_kde(ages)
        x = linspace(xmi, xma, N)
        y = pdf(x)

        return x, y

    def _cumulative_probability(self, ages, errors, xmi, xma):
        bins = linspace(xmi, xma, N)
        probs = zeros(N)

        for ai, ei in zip(ages, errors):
            if abs(ai) < 1e-10 or abs(ei) < 1e-10:
                continue

            # calculate probability curve for ai+/-ei
            # p=1/(2*pi*sigma2) *exp (-(x-u)**2)/(2*sigma2)
            # see http://en.wikipedia.org/wiki/Normal_distribution
            ds = (ones(N) * ai - bins) ** 2
            es = ones(N) * ei
            es2 = 2 * es * es
            gs = (es2 * pi) ** -0.5 * exp(-ds / es2)

            # cumulate probabilities
            # numpy element_wise addition
            probs += gs

        return bins, probs

    def _calculate_nominal_xlimits(self):
        return self.min_x(self.options.index_attr), self.max_x(self.options.index_attr)

    def _calculate_asymptotic_limits(self, cfunc, max_iter=200, asymptotic_width=10,
                                     tol=10):
        """
            cfunc: callable that returns xs,ys and accepts xmin, xmax
                    xs, ys= cfunc(x1,x2)

            asymptotic_width=percent of total width that is less than tol% of the total curve

            returns xs,ys,xmi,xma
        """
        tol *= 0.01
        rx1, rx2 = None, None
        xmi, xma = self._calculate_nominal_xlimits()
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

        #if tt is not None:
        #    self.graph.add_horizontal_rule(tt)

        if rx1 is None:
            rx1 = x1
        if rx2 is None:
            rx2 = x2

        return xs, ys, rx1, rx2

    def _cmp_analyses(self, x):
        return x.age

    def _calculate_stats(self, xs, ys):
        ag = self.analysis_group
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

            # wm, we = calculate_weighted_mean(ages, errors)
            # we = self._calc_error(we, mswd)

        return wm, we * self.options.nsigma, mswd, valid_mswd

        # def _calc_error(self, we, mswd):
        #     ec = self.options.error_calc_method
        #     n = self.options.nsigma
        #     if ec == 'SEM':
        #         a = 1
        #     elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
        #         a = 1
        #         if mswd > 1:
        #             a = mswd ** 0.5
        #     return we * a * n


        #============= EOF =============================================
        #def _add_mean_indicator2(self, g, scatter, bins, probs, pid):
        #        offset = 0
        #        percentH = 1 - 0.954  # 2sigma
        #
        #        maxp = max(probs)
        #        wm, we, mswd, valid_mswd = self._calculate_stats(self.xs, self.xes,
        #                                                         bins, probs)
        #        #ym = maxp * percentH + offset
        #        #set ym in screen space
        #        #convert to data space
        #        ogid = self.group_id
        #        gid = ogid + 1
        #        sgid = ogid * 3
        #
        #        ym = maxp * 0.1 * gid
        #
        #        s, p = g.new_series(
        #            [wm], [ym],
        #            type='scatter',
        #                            marker='circle',
        #                            #selection_marker_size=3,
        #                            marker_size=3,
        #                            #selection_marker='circle',
        #                            #selection_color=scatter.color,
        #                            #selection_outline_color=scatter.color,
        #                            color=scatter.color,
        #                            plotid=0
        #        )
        #
        #        g.set_series_label('Mean-{}'.format(gid), series=sgid + 2, plotid=pid)
        #
        #        self._add_error_bars(s, [we], 'x', self.options.nsigma)
        #        #         display_mean_indicator = self._get_plot_option(self.options, 'display_mean_indicator', default=True)
        #        if not self.options.display_mean_indicator:
        #            s.visible = False
        #
        #        label = None
        #        #         display_mean = self._get_plot_option(self.options, 'display_mean_text', default=True)
        #        if self.options.display_mean:
        #            text = self._build_label_text(wm, we, mswd, valid_mswd, len(self.xs))
        #            #             font = self._get_plot_option(self.options, 'data_label_font', default='modern 12')
        #            self._add_data_label(s, text, (wm, ym),
        #                                 #                                 font=font
        #            )
        #            # add a tool to move the mean age point
        #        s.tools.append(PointMoveTool(component=s,
        #                                     label=label,
        #                                     constrain='y'))