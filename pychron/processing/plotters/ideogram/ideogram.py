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
from chaco.plot_label import PlotLabel
from traits.api import Float, Array
#============= standard library imports ========================
from numpy import linspace, pi, exp, zeros, ones, array, arange, \
    Inf
#============= local library imports  ==========================

from pychron.processing.plotters.arar_figure import BaseArArFigure

from pychron.processing.plotters.ideogram.mean_indicator_overlay import MeanIndicatorOverlay
from pychron.stats.peak_detection import find_peaks
from pychron.stats.core import calculate_weighted_mean
from pychron.processing.plotters.point_move_tool import OverlayMoveTool

N = 500


class Ideogram(BaseArArFigure):
    xmi = Float
    xma = Float
    xs = Array
    xes = Array
    index_key = 'uage'
    ytitle = 'Relative Probability'
    #     _reverse_sorted_analyses = True
    _analysis_number_cnt = 0

    x_grid_visible = False
    y_grid_visible = False

    def plot(self, plots):
        """
            plot data on plots
        """

        graph = self.graph

        self._analysis_number_cnt = 0

        try:
            self.xs, self.xes = array([(ai.nominal_value, ai.std_dev)
                                   for ai in self._get_xs(key=self.index_key)]).T
        except ValueError:
            return

        omit = self._get_omitted(self.sorted_analyses,
                                 omit='omit_ideo')
        omit=set(omit)
        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            args=getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)
            if args:
                scatter, omits=args
                for i,ai in enumerate(self.sorted_analyses):
                    ai.filter_omit=i in omits

                omit=omit.union(set(omits))

        graph.set_x_limits(min_=self.xmi, max_=self.xma,
                           pad='0.05')

        ref = self.analyses[0]
        age_units = ref.arar_constants.age_units
        graph.set_x_title('Age ({})'.format(age_units))

        #turn off ticks for prob plot by default
        plot = graph.plots[0]
        plot.value_axis.tick_label_formatter = lambda x: ''
        plot.value_axis.tick_visible = False

        print 'ideo omit', self.group_id, omit, plots
        if omit:
            self._rebuild_ideo(list(omit))

    def max_x(self, attr):
        try:
            return max([ai.nominal_value + ai.std_dev
                    for ai in self._unpack_attr(attr)])
        except ValueError:
            return 0

    def min_x(self, attr):
        try:
            return min([ai.nominal_value - ai.std_dev
                    for ai in self._unpack_attr(attr)])
        except ValueError:
            return 0


    #===============================================================================
    # plotters
    #===============================================================================

    def _plot_aux(self, title, vk, ys, po, plot, pid,
                  es=None):

        omits=self._get_aux_plot_omits(po, ys)

        scatter = self._add_aux_plot(ys,
                                     title, pid)

        self._add_error_bars(scatter, self.xes, 'x', 1,
                             visible=po.x_error)
        if es:
            self._add_error_bars(scatter, es, 'y', 1,
                                 visible=po.y_error)

        if po.show_labels:
            self._add_point_labels(scatter)

        self._add_scatter_inspector(scatter)
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
                if p.y_axis.title == name:
                    for k, rend in p.plots.iteritems():
                        if k.startswith(name):
                            startidx += rend[0].index.get_size()

        ys = arange(startidx, startidx + n)

        scatter = self._add_aux_plot(ys, name, pid)

        self._add_error_bars(scatter, self.xes, 'x', 1,
                             visible=po.x_error)

        self._add_scatter_inspector(scatter,
                                    value_format=lambda x: '{:d}'.format(int(x)),
                                    additional_info=lambda x: u'Age= {}'.format(x.age_string))
        if po.show_labels:
            self._add_point_labels(scatter)

        #         self._analysis_number_cnt += n
        self.graph.set_y_limits(min_=0,
                                max_=max(ys) + 1,
                                plotid=pid)

        omits=self._get_aux_plot_omits(po, ys)
        return scatter, omits

    def _plot_relative_probability(self, po, plot, pid):
        graph = self.graph
        bins, probs = self._calculate_probability_curve(self.xs, self.xes)

        ogid = self.group_id
        gid = ogid + 1
        sgid = ogid * 2

        scatter, _p = graph.new_series(x=bins, y=probs, plotid=pid)
        graph.set_series_label('Current-{}'.format(gid), series=sgid, plotid=pid)

        # add the dashed original line
        graph.new_series(x=bins, y=probs,
                         plotid=pid,
                         visible=False,
                         color=scatter.color,
                         line_style='dash',
        )
        graph.set_series_label('Original-{}'.format(gid), series=sgid + 1, plotid=pid)

        self._add_info(graph, plot)
        self._add_mean_indicator(graph, scatter, bins, probs, pid)
        mi, ma = min(probs), max(probs)
        self._set_y_limits(mi, ma, min_=0)

        d = lambda a, b, c, d: self.update_index_mapper(a, b, c, d)
        plot.index_mapper.on_trait_change(d, 'updated')

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
            m = self.options.mean_calculation_kind
            e = self.options.error_calc_method
            s = self.options.nsigma
            if self.options.show_info:
                pl = PlotLabel(text=u'Mean: {} +/-{}s\nError Type: {}'.format(m, s, e),
                               overlay_position='inside top',
                               hjustify='left',
                               component=plot)
                plot.overlays.append(pl)

    def _add_mean_indicator(self, g, line, bins, probs, pid):
        maxp = max(probs)
        wm, we, mswd, valid_mswd = self._calculate_stats(self.xs, self.xes,
                                                         bins, probs)
        #ym = maxp * percentH + offset
        #set ym in screen space
        #convert to data space
        ogid = self.group_id
        gid = ogid + 1
        sgid = ogid * 2

        text = ''
        if self.options.display_mean:
            text = self._build_label_text(wm, we, mswd, valid_mswd, len(self.xs))

        m = MeanIndicatorOverlay(component=line,
                                 x=wm,
                                 y=20 * gid,
                                 error=we,
                                 nsgima=self.options.nsigma,
                                 color=line.color,
                                 text=text,
                                 visibile=self.options.display_mean_indicator
        )
        line.overlays.append(m)

        line.tools.append(OverlayMoveTool(component=m,
                                          constrain='x'))

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
            print 'update graph meta'
            self._rebuild_ideo(sel)


    def _rebuild_ideo(self, sel):
        print 'rebuild ideo {}'.format(sel)
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
            wm, we, mswd, valid_mswd = self._calculate_stats(fxs, fxes, xs, ys)

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
                    ov.label.text = self._build_label_text(wm, we, mswd, valid_mswd, n)

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

    def _add_aux_plot(self, ys, title, pid, **kw):
        plot = self.graph.plots[pid]
        if plot.value_scale == 'log':
            ys = array(ys)
            ys[ys < 0] = 1e-20

        graph = self.graph
        graph.set_y_title(title,
                          plotid=pid)

        #print 'aux plot',title, self.group_id
        s, p = graph.new_series(
            x=self.xs, y=ys,
            type='scatter',
            marker='circle',
            marker_size=3,
            selection_marker_size=3,
            bind_id=self.group_id,
            plotid=pid, **kw)

        graph.set_series_label('{}-{}'.format(title, self.group_id + 1),
                               plotid=pid)
        return s

    def _calculate_probability_curve(self, ages, errors):

        xmi, xma = self.graph.get_x_limits()
        if xmi == -Inf or xma == Inf:
            xmi, xma = self.xmi, self.xma

        #        print self.probability_curve_kind
        if self.options.probability_curve_kind == 'kernel':
            return self._kernel_density(ages, errors, xmi, xma)

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
            # p=1/(2*p*sigma2) *exp (-(x-u)**2)/(2*sigma2)
            # see http://en.wikipedia.org/wiki/Normal_distribution
            ds = (ones(N) * ai - bins) ** 2
            es = ones(N) * ei
            es2 = 2 * es * es
            gs = (es2 * pi) ** -0.5 * exp(-ds / es2)

            # cumulate probabilities
            # numpy element_wise addition
            probs += gs

        return bins, probs

    def _cmp_analyses(self, x):
        return x.age

    def _calculate_stats(self, ages, errors, xs, ys):
        mswd, valid_mswd, n = self._get_mswd(ages, errors)
        #         mswd = calculate_mswd(ages, errors)
        #         valid_mswd = validate_mswd(mswd, len(ages))
        if self.options.mean_calculation_kind == 'kernel':
            wm, we = 0, 0
            delta = 1
            maxs, _mins = find_peaks(ys, xs, delta=delta, lookahead=1)
            wm = max(maxs, axis=1)[0]
        else:
            wm, we = calculate_weighted_mean(ages, errors)
            we = self._calc_error(we, mswd)

        return wm, we, mswd, valid_mswd

    def _calc_error(self, we, mswd):
        ec = self.options.error_calc_method
        n = self.options.nsigma
        if ec == 'SEM':
            a = 1
        elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
            a = 1
            if mswd > 1:
                a = mswd ** 0.5
        return we * a * n


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