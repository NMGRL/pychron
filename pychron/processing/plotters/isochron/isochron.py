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

#============= enthought library imports =======================
from chaco.abstract_overlay import AbstractOverlay
from enable.enable_traits import LineStyle
from kiva.trait_defs.kiva_font_trait import KivaFont
from traits.api import Array, Float, Str
from chaco.plot_label import PlotLabel
from chaco.array_data_source import ArrayDataSource
#============= standard library imports ========================
from numpy import linspace
#============= local library imports  ==========================

from pychron.core.helpers.formatting import floatfmt, calc_percent_error, format_percent_error
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.processing.argon_calculations import extract_isochron_xy
from pychron.processing.plotters.arar_figure import BaseArArFigure

from pychron.graph.error_ellipse_overlay import ErrorEllipseOverlay
from pychron.core.stats import validate_mswd



class OffsetPlotLabel(PlotLabel):
    offset = None

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
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

        with gc:
            gc.set_line_width(self.line_width)
            gc.set_line_dash(self.line_style_)
            gc.move_to(xo, y)
            gc.line_to(x, y)
            gc.draw_path()

            txt = self.label
            gc.set_font(self.font)
            w, h = gc.get_full_text_extent(txt)[:2]
            gc.set_text_position(xo - w - 2, y)
            gc.show_text(txt)


class Isochron(BaseArArFigure):
    _omit_key = 'omit_iso'


class InverseIsochron(Isochron):
    #     xmi = Float
    #     xma = Float

    xs = Array
    _cached_data = None
    _plot_label = None
    suppress = False
    xpad = '0.1'

    def plot(self, plots):
        """
            plot data on plots
        """
        graph = self.graph

        #self._plot_inverse_isochron(graph.plots[0], 0)

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)

        #for si in self.sorted_analyses:
        #    print si.record_id, si.group_id

        omit = self._get_omitted(self.sorted_analyses)
        #print 'iso omit', omit
        if omit:
            self._rebuild_iso(omit)

    # ===============================================================================
    # plotters
    # ===============================================================================
    def _plot_aux(self, title, vk, ys, po, plot, pid, es=None):
        scatter = self._add_aux_plot(ys, title, vk, pid)

    def _add_plot(self, xs, ys, es, plotid, value_scale='linear'):
        pass

    def _plot_inverse_isochron(self, po, plot, pid):
        analyses = self.sorted_analyses
        plot.padding_left = 75

        refiso = analyses[0]

        self._ref_constants = refiso.arar_constants
        self._ref_j = refiso.j
        self._ref_age_scalar = refiso.arar_constants.age_scalar
        self._ref_age_units = refiso.arar_constants.age_units

        # try:
        #     age, reg, data = calculate_isochron(analyses)
        # except TypeError:
        #     return
        data = self.analysis_group.get_isochron_data()

        _, reg, (xs, ys, xerrs, yerrs) = data
        self._cached_data = data
        self._cached_reg = reg

        graph = self.graph
        graph.set_x_title('39Ar/40Ar', plotid=pid)
        graph.set_y_title('36Ar/40Ar', plotid=pid)
        p = graph.plots[pid]
        p.y_axis.title_spacing = 50

        graph.set_grid_traits(visible=False)
        graph.set_grid_traits(visible=False, grid='y')

        scatter, _p = graph.new_series(xs, ys,
                                       xerror=ArrayDataSource(data=xerrs),
                                       yerror=ArrayDataSource(data=yerrs),
                                       type='scatter',
                                       marker='circle',
                                       bind_id=self.group_id,
                                       #selection_marker_size=5,
                                       #selection_color='green',
                                       marker_size=2)
        #self._scatter = scatter
        graph.set_series_label('data{}'.format(self.group_id))

        eo = ErrorEllipseOverlay(component=scatter,
                                 reg=reg,
                                 fill=self.options.fill_ellipses)
        scatter.overlays.append(eo)

        # mi, ma = graph.get_x_limits()

        # ma = max(ma, max(xs))
        # mi = min(mi, min(xs))
        mi, ma = min(xs), max(xs)
        # print len(xs),mi,ma
        mi = 0
        rxs = linspace(mi, ma)
        rys = reg.predict(rxs)

        graph.set_x_limits(min_=mi, max_=ma, pad='0.1')

        l, _ = graph.new_series(rxs, rys, color=scatter.color)
        graph.set_series_label('fit{}'.format(self.group_id))

        l.index.set_data(rxs)
        l.value.set_data(rys)
        xs = l.index.get_data()
        lci, uci = reg.calculate_error_envelope(xs)
        ee = ErrorEnvelopeOverlay(component=l,
                                  upper=uci, lower=lci)
        l.underlays.append(ee)
        l.error_envelope = ee

        def ad(ai):
            a = ai.isotopes['Ar39'].get_interference_corrected_value()
            b = ai.isotopes['Ar40'].get_interference_corrected_value()
            r = a / b
            v = r.nominal_value
            e = r.std_dev

            try:
                pe = '({:0.2f}%)'.format(e / v * 100)
            except ZeroDivisionError:
                pe = '(Inf%)'

            return '39Ar/40Ar = {} +/-{} {}'.format(floatfmt(v, n=6), floatfmt(e, n=7), pe)

        graph.add_vertical_rule(0, color='black')
        self._add_info(plot, reg, text_color=scatter.color)

        if self.options.show_nominal_intercept:
            self._add_atm_overlay(plot)

        if po.show_labels:
            self._add_point_labels(scatter)

        self._add_scatter_inspector(scatter, additional_info=ad)

    # ===============================================================================
    # overlays
    # ===============================================================================

    def _add_atm_overlay(self, plot):
        v = self.options.nominal_intercept_value
        plot.overlays.append(AtmInterceptOverlay(component=plot,
                                                 label=self.options.nominal_intercept_label,
                                                 value=v))

    def _add_info(self, plot, reg, label=None, text_color='black'):
        intercept = reg.predict(0)
        err = reg.get_intercept_error()
        mswd = reg.mswd
        n = reg.n

        try:
            inv_intercept = intercept ** -1
            p = calc_percent_error(intercept, err, scale=1)

            err = inv_intercept * p
            mse = err * mswd ** 0.5
            v, e, p, mse = floatfmt(inv_intercept, s=3), floatfmt(err, s=3), floatfmt(p * 100, n=2), floatfmt(mse, s=3)
        except ZeroDivisionError:
            v, e, p, mse = 'NaN', 'NaN', 'NaN', 'NaN'

        ratio_line = 'Ar40/Ar36= {} +/-{} ({}%) mse= {}'.format(v, e, p, mse)

        u = self._ref_age_units

        age = self.analysis_group.isochron_age

        v = age.nominal_value
        e = age.std_dev
        p = format_percent_error(v, e)

        mse_age = e * mswd ** 0.5

        valid = validate_mswd(mswd, n)
        mswd = '{:0.2f}'.format(mswd)
        if not valid:
            mswd = '*{}'.format(mswd)
            #n = len([ai for ai in self.analyses if ai.temp_status == 0])
        #mswd = 'NaN'
        age_line = 'Age= {} +/-{} ({}%) {}. mse= {}'.format(floatfmt(v, n=3),
                                                            floatfmt(e, n=4, s=3), p, u,
                                                            floatfmt(mse_age, s=3))
        mswd_line = 'N= {} mswd= {}'.format(n, mswd)
        if label is None:
            label = OffsetPlotLabel(
                offset=(1, 1 + 50 * self.group_id),
                component=plot,
                overlay_position='inside bottom',
                hjustify='left',
                bgcolor='white',

                color=text_color)
            plot.overlays.append(label)
            self._plot_label = label

        lines = '\n'.join((ratio_line, age_line, mswd_line))
        label.text = '{}'.format(lines)
        label.request_redraw()

    def replot(self):
        self.suppress = True

        om = self._get_omitted(self.sorted_analyses)
        self._rebuild_iso(om)
        self.suppress = False

    def _rebuild_iso(self, sel):
        g = self.graph
        ss = [p.plots[pp][0] for p in g.plots
              for pp in p.plots
              if pp == 'data{}'.format(self.group_id)]

        self._set_renderer_selection(ss, sel)

        if self._cached_data:
            reg = self._cached_reg

            reg.user_excluded = sel
            reg.dirty = True
            reg.error_calc_type= self.options.error_calc_method
            reg.calculate()

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

            if self._plot_label:
                self._add_info(self.graph.plots[0], reg, label=self._plot_label)

    def update_graph_metadata(self, obj, name, old, new):
        if obj:
            self._filter_metadata_changes(obj, self._rebuild_iso, self.analyses)

    def update_index_mapper(self, obj, name, old, new):
        if new is True:
            self.update_graph_metadata(None, name, old, new)

    # ===============================================================================
    # utils
    # ===============================================================================
    def max_x(self, *args):
        xx, yy = extract_isochron_xy(self.analyses)
        try:
            return max([ai.nominal_value + ai.std_dev
                        for ai in xx])
        except (AttributeError, ValueError):
            return 0

    def min_x(self, *args):
        xx, yy = extract_isochron_xy(self.analyses)
        try:
            return min([ai.nominal_value - ai.std_dev
                        for ai in xx])
        except (AttributeError, ValueError):
            return 0

    def _add_aux_plot(self, ys, title, vk, pid, **kw):
        graph = self.graph
        graph.set_y_title(title,
                          plotid=pid)

        xs, ys, es, _ = self._calculate_spectrum(value_key=vk)
        s = self._add_plot(xs, ys, es, pid, **kw)
        return s

        # def _get_age_errors(self, ans):
        #     ages, errors = zip(*[(ai.age.nominal_value,
        #                           ai.age.std_dev)
        #                          for ai in self.sorted_analyses])
        #     return array(ages), array(errors)

        #def _calculate_stats(self, ages, errors, xs, ys):
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

        #def _calc_error(self, we, mswd):
        #    ec = self.options.error_calc_method
        #    n = self.options.nsigma
        #    if ec == 'SEM':
        #        a = 1
        #    elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
        #        a = 1
        #        if mswd > 1:
        #            a = mswd ** 0.5
        #    return we * a * n
        #def _calculate_individual_ages(self, include_j_err=False):
        #from numpy import polyfit
        #reg=ReedYorkRegressor()
        #def func(ai):
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
        #return zip(*[func(aa) for aa in self.analyses])


# ===============================================================================
# labels
# ===============================================================================
#     def _build_integrated_age_label(self, tga, *args):
#         age, error = tga.nominal_value, tga.std_dev
#         error *= self.options.nsigma
#         txt = self._build_label_text(age, error, *args)
#         return 'Integrated Age= {}'.format(txt)

# ============= EOF =============================================
