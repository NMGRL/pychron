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
from chaco.label import Label
from chaco.plot_label import PlotLabel
from enable.enable_traits import LineStyle
from kiva import FILL
from kiva.trait_defs.kiva_font_trait import KivaFont
from numpy import linspace, pi
from six.moves import zip
from traits.api import Float, Str, Instance
from uncertainties import std_dev, nominal_value

from pychron.core.helpers.formatting import (
    floatfmt,
    calc_percent_error,
    format_percent_error,
)
from pychron.core.stats import validate_mswd
from pychron.graph.error_ellipse_overlay import ErrorEllipseOverlay
from pychron.graph.error_envelope_overlay import ErrorEnvelopeOverlay
from pychron.graph.ml_label import tokenize
from pychron.pipeline.plot.overlays.isochron_inset import (
    InverseIsochronPointsInset,
    InverseIsochronLineInset,
)
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.pychron_constants import PLUSMINUS, SIGMA, MSEM, SEM, SE, MSE


class MLTextLabel(Label):
    def _calc_line_positions(self, gc):
        """
        need to modify from Label so that the width is not
        overestimated. since there can be tags that when rendered don't
        take up any width

        so replace <sub> </sub> <sup> </sup> with ''
        then calculate bounding box

        :param gc:
        :return:
        """
        if not self._position_cache_valid:
            with gc:
                gc.set_font(self.font)
                # The bottommost line starts at postion (0, 0).
                x_pos = []
                y_pos = []
                self._bounding_box = [0, 0]
                margin = self.margin
                prev_y_pos = margin
                prev_y_height = -self.line_spacing
                max_width = 0

                text = self.text
                for a in ("sub", "sup"):
                    text = text.replace("<{}>".format(a), "")
                    text = text.replace("</{}>".format(a), "")

                for line in text.split("\n")[::-1]:
                    if line != "":
                        (width, height, descent, leading) = gc.get_full_text_extent(
                            line
                        )
                        ascent = height - abs(descent)
                        if width > max_width:
                            max_width = width
                        new_y_pos = prev_y_pos + prev_y_height + self.line_spacing
                    else:
                        # For blank lines, we use the height of the previous
                        # line, if there is one.  The width is 0.
                        leading = 0
                        if prev_y_height != -self.line_spacing:
                            new_y_pos = prev_y_pos + prev_y_height + self.line_spacing
                            ascent = prev_y_height
                        else:
                            new_y_pos = prev_y_pos
                            ascent = 0
                    x_pos.append(-leading + margin)
                    y_pos.append(new_y_pos)
                    prev_y_pos = new_y_pos
                    prev_y_height = ascent

            self._line_xpos = x_pos[::-1]
            self._line_ypos = y_pos[::-1]
            border_width = self.border_width if self.border_visible else 0

            self._bounding_box[0] = max_width + 2 * margin + 2 * border_width
            self._bounding_box[1] = (
                prev_y_pos + prev_y_height + margin + 2 * border_width
            )
            self._position_cache_valid = True
        return

    def draw(self, gc):
        """Draws the label.

        This method assumes the graphics context has been translated to the
        correct position such that the origin is at the lower left-hand corner
        of this text label's box.
        """
        # Make sure `max_width` is respected
        self._fit_text_to_max_width(gc)

        # For this version we're not supporting rotated text.
        self._calc_line_positions(gc)

        with gc:
            bb_width, bb_height = self.get_bounding_box(gc)

            # Rotate label about center of bounding box
            width, height = self._bounding_box
            gc.translate_ctm(bb_width / 2.0, bb_height / 2.0)
            gc.rotate_ctm(pi / 180.0 * self.rotate_angle)
            gc.translate_ctm(-width / 2.0, -height / 2.0)

            # Draw border and fill background
            if self.bgcolor != "transparent":
                gc.set_fill_color(self.bgcolor_)
                gc.draw_rect((0, 0, width, height), FILL)
            if self.border_visible and self.border_width > 0:
                gc.set_stroke_color(self.border_color_)
                gc.set_line_width(self.border_width)
                border_offset = (self.border_width - 1) / 2.0
                gc.rect(
                    border_offset,
                    border_offset,
                    width - 2 * border_offset,
                    height - 2 * border_offset,
                )
                gc.stroke_path()

            gc.set_fill_color(self.color_)
            gc.set_stroke_color(self.color_)
            gc.set_font(self.font)
            if self.font.size <= 8.0:
                gc.set_antialias(0)
            else:
                gc.set_antialias(1)

            lines = self.text.split("\n")
            if self.border_visible:
                gc.translate_ctm(self.border_width, self.border_width)

            # width, height = self.get_width_height(gc)
            for i, line in enumerate(lines):
                if line == "":
                    continue
                x_offset = round(self._line_xpos[i])
                y_offset = round(self._line_ypos[i])

                self._draw_line(gc, line, x_offset, y_offset)
                # with gc:
                # gc.translate_ctm(x_offset, y_offset)

                # self._draw_line(gc, line)

    def _draw_line(self, gc, txt, xo, yo):
        def gen():
            offset = 0
            for ti in tokenize(txt):
                if ti == "sup":
                    offset = 1
                elif ti == "sub":
                    offset = -1
                elif ti in ("/sup", "/sub"):
                    offset = 0
                else:
                    yield offset, ti

        ofont = self.font
        sfont = self.font.copy()
        sfont.size = int(sfont.size * 0.80)
        suph = int(ofont.size * 0.4)
        subh = -int(ofont.size * 0.3)

        x = 0
        for offset, text in gen():
            with gc:
                yoff = yo
                if offset == 1:
                    # gc.translate_ctm(0, suph)
                    gc.set_font(sfont)
                    yoff += suph
                elif offset == -1:
                    # gc.translate_ctm(0, subh)
                    gc.set_font(sfont)
                    yoff += subh
                else:
                    gc.set_font(ofont)

                w, h, _, _ = gc.get_full_text_extent(text)
                gc.set_text_position(x + xo, yoff)
                gc.show_text(text)
                x += w


class OffsetPlotLabel(PlotLabel):
    offset = None
    _label = Instance(MLTextLabel, args=())

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        with gc:
            if self.offset:
                gc.translate_ctm(*self.offset)
            super(OffsetPlotLabel, self).overlay(component, gc, view_bounds, mode)


class AtmInterceptOverlay(AbstractOverlay):
    line_width = Float(1.5)
    font = KivaFont("modern 10")
    line_style = LineStyle("dash")
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

            gc.clip_to_rect(
                component.x - w - 5, component.y, component.width, component.height
            )

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
    _analysis_group_klass = StepHeatAnalysisGroup

    def post_make(self):
        g = self.graph
        for i, p in enumerate(g.plots):
            l, h = self.ymis[i], self.ymas[i]
            g.set_y_limits(max(0, l), h, pad="0.1", pad_style="upper", plotid=i)

        g.set_x_limits(0, self.xma * 1.1)
        self._fix_log_axes()

    def plot(self, plots, legend=None):
        """
        plot data on plots
        """
        graph = self.graph

        if self.options.omit_non_plateau:
            self.analysis_group.do_omit_non_plateau()

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            plot_name = po.plot_name
            if not plot_name:
                continue
            getattr(self, "_plot_{}".format(plot_name))(po, plotobj, pid)

    # ===============================================================================
    # plotters
    # ===============================================================================
    def _plot_aux(self, vk, po, pid):
        title = po.get_ytitle(vk)
        ys, es = self._get_aux_plot_data(vk, po.scalar)
        self._add_aux_plot(ys, title, vk, pid)

    def _add_plot(self, xs, ys, es, plotid, value_scale="linear"):
        pass

    def _plot_inverse_isochron(self, po, plot, pid):
        opt = self.options
        self.analysis_group.isochron_age_error_kind = opt.error_calc_method
        self.analysis_group.isochron_method = opt.regressor_kind
        _, _, reg = self.analysis_group.get_isochron_data(
            exclude_non_plateau=opt.exclude_non_plateau
        )
        graph = self.graph

        xtitle = "<sup>39</sup>Ar/<sup>40</sup>Ar"
        ytitle = "<sup>36</sup>Ar/<sup>40</sup>Ar"

        # self._set_ml_title(ytitle, pid, 'y')
        # self._set_ml_title(xtitle, pid, 'x')
        graph.set_y_title(ytitle, plotid=pid)
        graph.set_x_title(xtitle, plotid=pid)

        p = graph.plots[pid]
        p.y_axis.title_spacing = 50

        graph.set_grid_traits(visible=False)
        graph.set_grid_traits(visible=False, grid="y")
        group = opt.get_group(self.group_id)
        color = group.color

        marker = opt.marker
        marker_size = opt.marker_size

        scatter, _p = graph.new_series(
            reg.xs,
            reg.ys,
            xerror=ArrayDataSource(data=reg.xserr),
            yerror=ArrayDataSource(data=reg.yserr),
            type="scatter",
            marker=marker,
            selection_marker=marker,
            selection_marker_size=marker_size,
            bind_id=self.group_id,
            color=color,
            marker_size=marker_size,
        )
        graph.set_series_label("data{}".format(self.group_id))

        eo = ErrorEllipseOverlay(
            component=scatter,
            reg=reg,
            border_color=color,
            fill=opt.fill_ellipses,
            kind=opt.ellipse_kind,
        )
        scatter.overlays.append(eo)

        ma = max(reg.xs)
        self.xma = max(self.xma, ma)
        self.xmi = min(self.xmi, min(reg.xs))

        mi = 0
        rxs = linspace(mi, ma * 1.1)
        rys = reg.predict(rxs)

        graph.set_x_limits(min_=mi, max_=ma, pad="0.1")

        l, _ = graph.new_series(rxs, rys, color=color)
        graph.set_series_label("fit{}".format(self.group_id))

        l.index.set_data(rxs)
        l.value.set_data(rys)
        yma, ymi = max(rys), min(rys)

        try:
            self.ymis[pid] = min(self.ymis[pid], ymi)
            self.ymas[pid] = max(self.ymas[pid], yma)
        except IndexError:
            self.ymis.append(ymi)
            self.ymas.append(yma)

        if opt.include_error_envelope:
            lci, uci = reg.calculate_error_envelope(l.index.get_data())
            ee = ErrorEnvelopeOverlay(
                component=l, upper=uci, lower=lci, line_color=color
            )
            l.underlays.append(ee)
            l.error_envelope = ee

        if opt.display_inset:
            self._add_inset(plot, reg)

        if self.group_id == 0:
            if opt.show_nominal_intercept:
                self._add_atm_overlay(plot)

            graph.add_vertical_rule(0, color="black")
        if opt.show_results_info:
            self._add_results_info(plot, text_color=color)
        if opt.show_info:
            self._add_info(plot)

        if opt.show_labels:
            self._add_point_labels(scatter)

        def ad(i, x, y, ai):
            a = ai.isotopes["Ar39"].get_interference_corrected_value()
            b = ai.isotopes["Ar40"].get_interference_corrected_value()
            r = a / b
            v = nominal_value(r)
            e = std_dev(r)

            try:
                pe = "({:0.2f}%)".format(e / v * 100)
            except ZeroDivisionError:
                pe = "(Inf%)"

            return "39Ar/40Ar= {} {} {} {}".format(
                floatfmt(v, n=6), PLUSMINUS, floatfmt(e, n=7), pe
            )

        self._add_scatter_inspector(scatter, additional_info=ad)
        p.index_mapper.on_trait_change(self.update_index_mapper, "updated")

        # sel = self._get_omitted_by_tag(self.analyses)
        # self._rebuild_iso(sel)
        self.replot()

    # ===============================================================================
    # overlays
    # ===============================================================================
    def _add_info(self, plot):
        ts = []
        if self.options.show_info:
            m = self.options.regressor_kind
            s = self.options.nsigma
            es = self.options.ellipse_kind
            ts.append(
                "{} {}{}{} Data: {}{}".format(m, PLUSMINUS, s, SIGMA, PLUSMINUS, es)
            )

        if self.options.show_error_type_info:
            ts.append("Error Type: {}".format(self.options.error_calc_method))

        if ts:
            self._add_info_label(plot, ts, font=self.options.info_font)

    def _add_inset(self, plot, reg):

        opt = self.options
        group = opt.get_group(self.group_id)
        insetp = InverseIsochronPointsInset(
            reg.xs,
            reg.ys,
            marker_size=opt.inset_marker_size,
            line_width=0,
            nominal_intercept=opt.inominal_intercept_value,
            label_font=opt.inset_label_font,
        )
        if opt.inset_show_error_ellipse:
            eo = ErrorEllipseOverlay(
                component=insetp,
                reg=reg,
                border_color=group.color,
                fill=opt.fill_ellipses,
                kind=opt.ellipse_kind,
            )
            insetp.overlays.append(eo)

        if self.group_id > 0:
            insetp.y_axis.visible = False
            insetp.x_axis.visible = False

        xintercept = reg.x_intercept * 1.1
        yintercept = reg.predict(0)
        m, _ = insetp.index.get_bounds()

        lx, hx = opt.inset_x_bounds

        if not lx and not hx:
            lx = -0.1 * (xintercept - m)
            hx = xintercept
        elif lx and lx > hx:
            hx = xintercept

        xs = linspace(lx, hx, 20)
        ys = reg.predict(xs)

        xtitle, ytitle = "", ""
        if opt.inset_show_axes_titles:
            xtitle = "<sup>39</sup>Ar/<sup>40</sup>Ar"
            ytitle = "<sup>36</sup>Ar/<sup>40</sup>Ar"

        insetl = InverseIsochronLineInset(
            xs, ys, xtitle=xtitle, ytitle=ytitle, label_font=opt.inset_label_font
        )
        plot.overlays.append(insetl)
        plot.overlays.append(insetp)

        ly, hy = opt.inset_y_bounds
        if not ly and not hy:
            ly = 0
            hy = max(1.1 * opt.inominal_intercept_value, yintercept * 1.1)
        elif hy < ly:
            hy = max(1.1 * opt.inominal_intercept_value, yintercept * 1.1)

        for inset in plot.overlays:
            if isinstance(
                inset, (InverseIsochronPointsInset, InverseIsochronLineInset)
            ):
                inset.location = opt.inset_location
                inset.width = opt.inset_width
                inset.height = opt.inset_height
                inset.color = group.color

                inset.index_range.low = lx
                inset.index_range.high = hx

                inset.value_range.low = ly
                inset.value_range.high = hy
        plot.request_redraw()

    def _add_atm_overlay(self, plot):
        plot.overlays.append(
            AtmInterceptOverlay(
                component=plot,
                label=self.options.nominal_intercept_label,
                value=self.options.inominal_intercept_value,
            )
        )

    def _add_results_info(self, plot, label=None, text_color="black"):

        ag = self.analysis_group

        age = ag.isochron_age
        a = ag.isochron_3640

        n = ag.nanalyses
        mswd = ag.isochron_regressor.mswd

        intercept, err = nominal_value(a), std_dev(a)

        opt = self.options
        try:
            inv_intercept = intercept**-1
            p = calc_percent_error(intercept, err, scale=1)
            err = inv_intercept * p * opt.nsigma
            mse = err * mswd**0.5
            sf = opt.yintercept_sig_figs
            v, e, p, mse = (
                floatfmt(inv_intercept, n=sf, s=3),
                floatfmt(err, n=sf, s=3),
                floatfmt(p * 100, n=2),
                floatfmt(mse, s=3),
            )
        except ZeroDivisionError:
            v, e, p, mse = "NaN", "NaN", "NaN", "NaN"

        sample_line = "{}({})".format(ag.identifier, ag.sample)
        mse_text = ""
        if opt.include_4036_mse:
            mse_text = " MSE= {}".format(mse)

        ptext = ""
        if opt.include_percent_error:
            ptext = " ({}%)".format(p)

        ratio_line = "<sup>40</sup>Ar/<sup>36</sup>Ar= {} {} {}{}{}".format(
            v, PLUSMINUS, e, ptext, mse_text
        )

        v = nominal_value(age)
        e = std_dev(age) * opt.nsigma

        if ag.isochron_age_error_kind in (MSE, MSEM):
            mse_age = e
        elif ag.isochron_age_error_kind in (SE, SEM):
            mse_age = e * mswd**0.5
        else:
            mse_age = 0

        valid = validate_mswd(mswd, n)
        mswd = "{:0.2f}".format(mswd)
        if not valid:
            mswd = "*{}".format(mswd)

        af = opt.age_sig_figs

        mse_text = ""
        if opt.include_age_mse:
            mse_text = " MSE= {}".format(floatfmt(mse_age, s=3))

        pe = ""
        if opt.include_age_percent_error:
            p = format_percent_error(v, e)
            pe = " ({})%".format(p)

        age_line = "Age={} {} {}{} {}{}".format(
            floatfmt(v, n=af),
            PLUSMINUS,
            floatfmt(e, n=af, s=3),
            pe,
            ag.age_units,
            mse_text,
        )
        mswd_line = "N={} MSWD={}".format(n, mswd)
        if label is None:
            th = 0
            for overlay in plot.overlays:
                if isinstance(overlay, OffsetPlotLabel):
                    w, h = overlay.get_preferred_size()
                    th += h + opt.results_info_spacing

            label = OffsetPlotLabel(
                offset=(1, th),
                component=plot,
                overlay_position="inside bottom",
                hjustify="left",
                bgcolor="transparent",
                font=opt.results_font,
                color=text_color,
            )
            plot.overlays.append(label)
            self._plot_label = label

        lines = [ratio_line, age_line, mswd_line]
        if opt.include_sample:
            lines.insert(0, sample_line)

        lines = "\n".join(lines)
        label.text = lines
        label.bgcolor = plot.bgcolor
        label.request_redraw()

    def replot(self):
        sel = self.analysis_group.get_omitted_by_tag(self.analyses)
        self._rebuild_iso(sel)

        # this is nonsensical and unnecessar
        # if len(sel) < self.analysis_group.nanalyses:s
        #     self._rebuild_iso(sel)

    def _rebuild_iso(self, sel=None):
        if not self.graph:
            return

        if sel is not None:
            g = self.graph
            ss = [
                p.plots[pp][0]
                for p in g.plots
                for pp in p.plots
                if pp == "data{}".format(self.group_id)
            ]
            self._set_renderer_selection(ss, sel)

        self.analysis_group.dirty = True
        if self._plot_label:
            self._add_results_info(self.graph.plots[0], label=self._plot_label)
        else:
            self.analysis_group.calculate_isochron()

        reg = self.analysis_group.isochron_regressor
        fit = self.graph.plots[0].plots["fit{}".format(self.group_id)][0]

        mi, ma = self.graph.get_x_limits()
        rxs = linspace(0, ma)

        rys = reg.predict(rxs)

        fit.index.set_data(rxs)
        fit.value.set_data(rys)

        if self.options.include_error_envelope:
            lci, uci = reg.calculate_error_envelope(rxs)
            if not hasattr(fit, "error_envelope"):
                group = self.options.get_group(self.group_id)
                color = group.color
                ee = ErrorEnvelopeOverlay(
                    component=fit, upper=uci, lower=lci, line_color=color
                )
                fit.underlays.append(ee)
                fit.error_envelope = ee
            else:

                fit.error_envelope.invalidate()

                fit.error_envelope.lower = lci
                fit.error_envelope.upper = uci

        if self.options.display_inset and self.options.inset_link_status:
            plot = self.graph.plots[self.group_id]
            if plot:
                for o in plot.overlays:
                    if isinstance(o, InverseIsochronLineInset):
                        o.index.set_data(rxs)
                        o.value.set_data(rys)

    def update_graph_metadata(self, obj, name, old, new):
        # print('asdfsdfasdfasd', obj, name, new)

        if obj:
            self._filter_metadata_changes(obj, self.sorted_analyses, self._rebuild_iso)

    def update_index_mapper(self, obj, name, old, new):
        # print('asdf', obj, name, new)
        if new:
            self.update_graph_metadata(None, name, old, new)

        if name == "updated":
            self.replot()

    # ===============================================================================
    # utils
    # ===============================================================================
    def _add_aux_plot(self, ys, title, vk, pid, **kw):
        graph = self.graph
        graph.set_y_title(title, plotid=pid)

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
