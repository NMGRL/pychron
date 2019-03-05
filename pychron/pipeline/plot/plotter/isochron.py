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
from __future__ import absolute_import

from chaco.abstract_overlay import AbstractOverlay
from chaco.array_data_source import ArrayDataSource
from chaco.plot_label import PlotLabel
from enable.enable_traits import LineStyle
from kiva.trait_defs.kiva_font_trait import KivaFont
from numpy import linspace
from six.moves import zip
from traits.api import Float, Str
from uncertainties import std_dev, nominal_value

from pychron.core.helpers.formatting import floatfmt, calc_percent_error, format_percent_error
from pychron.core.stats import validate_mswd
from pychron.graph.error_ellipse_overlay import ErrorEllipseOverlay
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.pipeline.plot.overlays.isochron_inset import InverseIsochronPointsInset, InverseIsochronLineInset
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
from pychron.pychron_constants import PLUSMINUS, SIGMA


class OffsetPlotLabel(PlotLabel):
    offset = None

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        with gc:
            if self.offset:
                gc.translate_ctm(*self.offset)
            super(OffsetPlotLabel, self).overlay(component, gc, view_bounds, mode)


class AtmInterceptOverlay(AbstractOverlay):
    line_width = Float(1.5)
    font = KivaFont("modern 10")
    line_style = LineStyle('dash')
    label = Str
    value = Float

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        x, y = component.map_screen((0, self.value))
        xo = component.x
        if x < xo:
            x = xo + 5

        with gc:
            txt = self.label
            gc.set_font(self.font)
            w, h = gc.get_full_text_extent(txt)[:2]

            gc.clip_to_rect(component.x - w - 5, component.y, component.width, component.height)

            gc.set_line_width(self.line_width)
            gc.set_line_dash(self.line_style_)
            gc.move_to(xo, y)
            gc.line_to(x, y)
            gc.draw_path()

            gc.set_text_position(xo - w - 2, y)
            gc.show_text(txt)


class Isochron(BaseArArFigure):
    pass


class InverseIsochron(Isochron):
    _plot_label = None
    xpad = None

    def post_make(self):
        g = self.graph
        for i, p in enumerate(g.plots):
            l, h = self.ymis[i], self.ymas[i]
            g.set_y_limits(max(0, l), h, pad='0.1', pad_style='upper', plotid=i)

        g.set_x_limits(0, self.xma, pad='0.1')
        self._fix_log_axes()

    def plot(self, plots, legend=None):
        """
            plot data on plots
        """
        graph = self.graph

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)

    # ===============================================================================
    # plotters
    # ===============================================================================
    def _plot_aux(self, title, vk, po, pid):
        ys, es = self._get_aux_plot_data(vk, po.scalar)
        self._add_aux_plot(ys, title, vk, pid)

    def _add_plot(self, xs, ys, es, plotid, value_scale='linear'):
        pass

    def _plot_inverse_isochron(self, po, plot, pid):
        self.analysis_group.isochron_age_error_kind = self.options.error_calc_method
        _, _, reg = self.analysis_group.get_isochron_data()

        # _, _, reg = data
        # self._cached_data = data
        # self._cached_reg = reg

        graph = self.graph

        xtitle = '<sup>39</sup>Ar/<sup>40</sup>Ar'
        ytitle = '<sup>36</sup>Ar/<sup>40</sup>Ar'

        # self._set_ml_title(ytitle, pid, 'y')
        # self._set_ml_title(xtitle, pid, 'x')
        graph.set_y_title(ytitle, plotid=pid)
        graph.set_x_title(xtitle, plotid=pid)

        p = graph.plots[pid]
        p.y_axis.title_spacing = 50

        graph.set_grid_traits(visible=False)
        graph.set_grid_traits(visible=False, grid='y')
        group = self.options.get_group(self.group_id)
        color = group.color

        scatter, _p = graph.new_series(reg.xs, reg.ys,
                                       xerror=ArrayDataSource(data=reg.xserr),
                                       yerror=ArrayDataSource(data=reg.yserr),
                                       type='scatter',
                                       marker='circle',
                                       bind_id=self.group_id,
                                       color=color,
                                       marker_size=2)
        graph.set_series_label('data{}'.format(self.group_id))

        eo = ErrorEllipseOverlay(component=scatter,
                                 reg=reg,
                                 border_color=color,
                                 fill=self.options.fill_ellipses,
                                 kind=self.options.ellipse_kind)
        scatter.overlays.append(eo)

        ma = max(reg.xs)
        self.xma = max(self.xma, ma)
        self.xmi = min(self.xmi, min(reg.xs))

        mi = 0
        rxs = linspace(mi, ma * 1.1)
        rys = reg.predict(rxs)

        graph.set_x_limits(min_=mi, max_=ma, pad='0.1')

        l, _ = graph.new_series(rxs, rys, color=color)
        graph.set_series_label('fit{}'.format(self.group_id))

        l.index.set_data(rxs)
        l.value.set_data(rys)
        yma, ymi = max(rys), min(rys)

        try:
            self.ymis[pid] = min(self.ymis[pid], ymi)
            self.ymas[pid] = max(self.ymas[pid], yma)
        except IndexError:
            self.ymis.append(ymi)
            self.ymas.append(yma)

        lci, uci = reg.calculate_error_envelope(l.index.get_data())
        ee = ErrorEnvelopeOverlay(component=l,
                                  upper=uci, lower=lci,
                                  line_color=color)
        l.underlays.append(ee)
        l.error_envelope = ee

        if self.options.display_inset:
            self._add_inset(plot, reg)

        if self.group_id == 0:
            if self.options.show_nominal_intercept:
                self._add_atm_overlay(plot)

            graph.add_vertical_rule(0, color='black')
        if self.options.show_results_info:
            self._add_results_info(plot, text_color=color)
        if self.options.show_info:
            self._add_info(plot)

        if self.options.show_labels:
            self._add_point_labels(scatter)

        def ad(i, x, y, ai):
            a = ai.isotopes['Ar39'].get_interference_corrected_value()
            b = ai.isotopes['Ar40'].get_interference_corrected_value()
            r = a / b
            v = nominal_value(r)
            e = std_dev(r)

            try:
                pe = '({:0.2f}%)'.format(e / v * 100)
            except ZeroDivisionError:
                pe = '(Inf%)'

            return u'39Ar/40Ar = {} {}{} {}'.format(floatfmt(v, n=6), PLUSMINUS, floatfmt(e, n=7), pe)

        self._add_scatter_inspector(scatter, additional_info=ad)
        p.index_mapper.on_trait_change(self.update_index_mapper, 'updated')

        sel = self._get_omitted_by_tag(self.analyses)
        self._rebuild_iso(sel)

    # ===============================================================================
    # overlays
    # ===============================================================================
    def _add_info(self, plot):
        ts = []
        if self.options.show_info:
            m = self.options.regressor_kind
            s = self.options.nsigma
            es = self.options.ellipse_kind
            ts.append(u'{} {}{}{} Data: {}{}'.format(m, PLUSMINUS, s, SIGMA, PLUSMINUS, es))

        if self.options.show_error_type_info:
            ts.append('Error Type: {}'.format(self.options.error_calc_method))

        if ts:
            self._add_info_label(plot, ts, font=self.options.info_font)

            # pl = FlowPlotLabel(text='\n'.join(ts),
            #                    overlay_position='inside top',
            #                    hjustify='left',
            #                    bgcolor=plot.bgcolor,
            #                    font=self.options.info_font,
            #                    component=plot)
            # plot.overlays.append(pl)

    def _add_inset(self, plot, reg):

        opt = self.options
        group = opt.get_group(self.group_id)
        color = group.color

        insetp = InverseIsochronPointsInset(reg.xs, reg.ys,
                                            marker_size=opt.inset_marker_size,
                                            color=color,
                                            line_width=0,
                                            # regressor=reg,
                                            nominal_intercept=opt.inominal_intercept_value,
                                            location=opt.inset_location,
                                            width=opt.inset_width,
                                            height=opt.inset_height,
                                            visible_axes=False)
        if self.group_id > 0:
            insetp.y_axis.visible = False
            insetp.x_axis.visible = False

        xintercept = reg.x_intercept * 1.1
        yintercept = reg.predict(0)
        m, _ = insetp.index.get_bounds()
        lx = -0.1 * (xintercept - m)
        hx = xintercept

        xs = linspace(lx, hx, 20)
        ys = reg.predict(xs)
        insetl = InverseIsochronLineInset(xs, ys,
                                          # regressor=reg,
                                          color=color,
                                          location=opt.inset_location,
                                          width=opt.inset_width,
                                          height=opt.inset_height)
        plot.overlays.append(insetl)
        plot.overlays.append(insetp)

        for inset in plot.overlays:
            if isinstance(inset, (InverseIsochronPointsInset, InverseIsochronLineInset)):
                inset.index_range.low = lx
                inset.index_range.high = hx

                inset.value_range.low = 0
                inset.value_range.high = max(1.1 * opt.inominal_intercept_value, yintercept * 1.1)

    def _add_atm_overlay(self, plot):
        plot.overlays.append(AtmInterceptOverlay(component=plot,
                                                 label=self.options.nominal_intercept_label,
                                                 value=self.options.inominal_intercept_value))

    def _add_results_info(self, plot, label=None, text_color='black'):

        ag = self.analysis_group

        age = ag.isochron_age
        a = ag.isochron_4036

        n = ag.nanalyses
        mswd = ag.isochron_regressor.mswd

        intercept, err = nominal_value(a), std_dev(a)

        try:
            inv_intercept = intercept ** -1
            p = calc_percent_error(intercept, err, scale=1)
            err = inv_intercept * p * self.options.nsigma
            mse = err * mswd ** 0.5
            sf = self.options.yintercept_sig_figs
            v, e, p, mse = floatfmt(inv_intercept, n=sf, s=3), floatfmt(err, n=sf, s=3), \
                           floatfmt(p * 100, n=2), floatfmt(mse, s=3)
        except ZeroDivisionError:
            v, e, p, mse = 'NaN', 'NaN', 'NaN', 'NaN'

        sample_line = u'{}({})'.format(ag.identifier, ag.sample)
        ratio_line = u'Ar40/Ar36= {} {}{} ({}%) mse= {}'.format(v, PLUSMINUS, e, p, mse)

        v = nominal_value(age)
        e = std_dev(age) * self.options.nsigma

        p = format_percent_error(v, e)

        mse_age = e * mswd ** 0.5

        valid = validate_mswd(mswd, n)
        mswd = '{:0.2f}'.format(mswd)
        if not valid:
            mswd = '*{}'.format(mswd)

        af = self.options.age_sig_figs
        age_line = u'Age= {} {}{} ({}%) {}. MSE= {}'.format(floatfmt(v, n=af),
                                                            PLUSMINUS,
                                                            floatfmt(e, n=af, s=3), p, ag.age_units,
                                                            floatfmt(mse_age, s=3))
        mswd_line = 'N= {} MSWD= {}'.format(n, mswd)
        if label is None:
            th = 0
            for overlay in plot.overlays:
                if isinstance(overlay, OffsetPlotLabel):
                    w, h = overlay.get_preferred_size()
                    th += h + self.options.results_info_spacing

            label = OffsetPlotLabel(
                offset=(1, th),
                component=plot,
                overlay_position='inside bottom',
                hjustify='left',
                bgcolor='white',
                font=self.options.results_font,
                color=text_color)
            plot.overlays.append(label)
            self._plot_label = label

        lines = u'\n'.join((sample_line, ratio_line, age_line, mswd_line))
        label.text = u'{}'.format(lines)
        label.bgcolor = plot.bgcolor
        label.request_redraw()

    def replot(self):
        # self.suppress = True
        # om = self._get_omitted(self.sorted_analyses)
        self._rebuild_iso()
        # self.suppress = False
        pass

    def _rebuild_iso(self, sel=None):
        if sel is not None:
            g = self.graph
            ss = [p.plots[pp][0] for p in g.plots
                  for pp in p.plots
                  if pp == 'data{}'.format(self.group_id)]

            self._set_renderer_selection(ss, sel)

        # reg = self._cached_reg
        #
        # reg.user_excluded = sel
        # reg.error_calc_type = self.options.error_calc_method
        # reg.dirty = True
        # reg.calculate()
        self.analysis_group.dirty = True
        if self._plot_label:
            self._add_results_info(self.graph.plots[0], label=self._plot_label)
        else:
            self.analysis_group.calculate_isochron()

        reg = self.analysis_group.isochron_regressor

        fit = self.graph.plots[0].plots['fit{}'.format(self.group_id)][0]

        mi, ma = self.graph.get_x_limits()
        rxs = linspace(0, ma)

        rys = reg.predict(rxs)

        fit.index.set_data(rxs)
        fit.value.set_data(rys)

        fit.error_envelope.invalidate()

        lci, uci = reg.calculate_error_envelope(rxs)
        fit.error_envelope.lower = lci
        fit.error_envelope.upper = uci

    def update_graph_metadata(self, obj, name, old, new):
        if obj:
            self._filter_metadata_changes(obj, self.analyses, self._rebuild_iso)

    def update_index_mapper(self, obj, name, old, new):
        if new:
            self.update_graph_metadata(None, name, old, new)

        if name == 'updated':
            self.replot()

    # ===============================================================================
    # utils
    # ===============================================================================
    def _add_aux_plot(self, ys, title, vk, pid, **kw):
        graph = self.graph
        graph.set_y_title(title,
                          plotid=pid)

        xs, ys, es, _ = self._calculate_spectrum(value_key=vk)
        self._add_plot(xs, ys, es, pid, **kw)

# ============= EOF =============================================
# def max_x(self, *args):
#     xx, yy = extract_isochron_xy(self.analyses)
#     try:
#         return max([ai.nominal_value + ai.std_dev
#                     for ai in xx])
#     except (AttributeError, ValueError):
#         return 0
#
# def min_x(self, *args):
#     xx, yy = extract_isochron_xy(self.analyses)
#     try:
#         return min([ai.nominal_value - ai.std_dev
#                     for ai in xx])
#     except (AttributeError, ValueError):
#         return 0
# def _get_age_errors(self, ans):
# ages, errors = zip(*[(ai.age.nominal_value,
# ai.age.std_dev)
# for ai in self.sorted_analyses])
# return array(ages), array(errors)

# def _calculate_stats(self, ages, errors, xs, ys):
#    mswd, valid_mswd, n = self._get_mswd(ages, errors)
#    #         mswd = calculate_mswd(ages, errors)
#    #         valid_mswd = validate_mswd(mswd, len(ages))
#    if self.options.mean_calculation_kind == 'kernel':
#        wm, we = 0, 0
#        delta = 1
#        maxs, _mins = find_peaks(ys, delta, xs)
#        wm = max(maxs, axis=1)[0]
#    else:
#        wm, we = calculate_weighted_mean(ages, errors)
#        we = self._calc_error(we, mswd)
#
#    return wm, we, mswd, valid_mswd

# def _calc_error(self, we, mswd):
#    ec = self.options.error_calc_method
#    n = self.options.nsigma
#    if ec == 'SEM':
#        a = 1
#    elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
#        a = 1
#        if mswd > 1:
#            a = mswd ** 0.5
#    return we * a * n
# def _calculate_individual_ages(self, include_j_err=False):
# from numpy import polyfit
# reg=ReedYorkRegressor()
# def func(ai):
#    a40,a39,a36=ai.Ar40, ai.Ar39, ai.Ar36
#    x,y=a39/a40, a36/a40
#
#    #x,y=x.nominal_value, y.nominal_value
#    #calculate fit with atmosphere
#    #x0,y0=0, 1/295.5
#    #m,b=polyfit([x,x0],[y,y0], 1)
#
#    xs=[0,x.nominal_value]
#    xserr=[0, x.std_dev]
#    ys=[1/295.5, y.nominal_value]
#    yserr=[0, y.std_dev]
#
#    print xs,ys
#    reg.trait_set(xs=xs, ys=ys, xserr=xserr, yserr=yserr)
#    reg.calculate()
#
#    R = ufloat(reg.x_intercept, reg.x_intercept_error)
#    print R
#    #inverse x_intercept
#    #R=(m/-b)
#    j=ai.j
#    if not include_j_err:
#        j=j.nominal_value
#
#    age=age_equation(j, R**-1, arar_constants=ai.arar_constants)
#    return age.nominal_value, age.std_dev
#
# return zip(*[func(aa) for aa in self.analyses])

# ===============================================================================
# labels
# ===============================================================================
# def _build_integrated_age_label(self, tga, *args):
# age, error = tga.nominal_value, tga.std_dev
# error *= self.options.nsigma
# txt = self._build_label_text(age, error, *args)
# return 'Integrated Age= {}'.format(txt)
