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

from math import isnan

from numpy import hstack, array

# ============= standard library imports ========================
from traits.api import Array, List, Instance, Dict
from uncertainties import nominal_value, std_dev

from pychron.pipeline.plot.overlays.label_overlay import (
    SpectrumLabelOverlay,
    RelativePlotLabel,
)
from pychron.pipeline.plot.overlays.spectrum import (
    SpectrumTool,
    SpectrumErrorOverlay,
    PlateauTool,
    PlateauOverlay,
    SpectrumInspectorOverlay,
)
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.pychron_constants import PLUSMINUS, SIGMA, MSEM


class Spectrum(BaseArArFigure):
    xs = Array
    spectrum_values = Dict
    _analysis_group_klass = StepHeatAnalysisGroup
    spectrum_overlays = List
    plateau_overlay = Instance(PlateauOverlay)
    age_label = None

    def plot(self, plots, legend=None):
        """
        plot data on plots
        """

        graph = self.graph

        ag = self.analysis_group

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            plot_name = po.plot_name
            if not plot_name:
                continue

            plot = getattr(self, "_plot_{}".format(plot_name))(po, plotobj, pid)

            if pid == 0:
                # self._set_ml_title('Cumulative %<sup>39</sup>Ar<sub>K</sub>', 0, 'x')
                graph.set_x_title("Cumulative %<sup>39</sup>Ar<sub>K</sub>", plotid=0)

            if legend and plot_name == "age_spectrum":
                ident = ag.identifier
                sample = ag.sample

                key = self.options.make_legend_key(ident, sample)
                if key in legend.plots:
                    ident = "{}-{:02d}".format(ident, ag.aliquot)
                    key = self.options.make_legend_key(ident, sample)

                legend.plots[key] = plot

    def max_x(self, attr):
        return max([ai.nominal_value for ai in self._unpack_attr(attr)])

    def min_x(self, attr):
        return min([ai.nominal_value for ai in self._unpack_attr(attr)])

    def mean_x(self, *args):
        return 50

    def get_ybounds(self, plotid=None, vs=None, s39=None, pma=None):
        if plotid is not None:
            xs, ys, es, c39s, s39, vs = self.spectrum_values[plotid]

        if s39 is None:
            s39 = self.s39

        ps = s39 / s39.sum()
        ps = ps > 0.01
        vs = vs[ps]
        # filter ys,es if 39Ar < 1% of total
        try:
            vs, es = zip(*[(nominal_value(vi), std_dev(vi)) for vi in vs])
            vs, es = array(vs), array(es)
            nes = es * self.options.step_nsigma
            yl = vs - nes
            yu = vs + nes

            _mi = min(yl)
            _ma = max(yu)
            if pma:
                _ma = max(pma, _ma)
        except ValueError:
            _mi = 0
            _ma = 1

        return _ma, _mi

    def calculate_ylimits(self, po, s39, vs, pma=None):
        # ps = s39 / s39.sum()
        # ps = ps > 0.01
        # vs = vs[ps]
        #
        # # filter ys,es if 39Ar < 1% of total
        # try:
        #     vs, es = zip(*[(nominal_value(vi), std_dev(vi)) for vi in vs])
        #     vs, es = array(vs), array(es)
        #     nes = es * self.options.step_nsigma
        #     yl = vs - nes
        #     yu = vs + nes
        #
        #     _mi = min(yl)
        #     _ma = max(yu)
        #     if pma:
        #         _ma = max(pma, _ma)
        # except ValueError:
        #     _mi = 0
        #     _ma = 1
        _ma, _mi = self.get_ybounds(vs=vs, s39=s39, pma=pma)
        if not po.has_ylimits():
            if po.calculated_ymin is None:
                po.calculated_ymin = _mi
            else:
                po.calculated_ymin = min(po.calculated_ymin, _mi)

            if po.calculated_ymax is None:
                po.calculated_ymax = _ma
            else:
                po.calculated_ymax = max(po.calculated_ymax, _ma)

    # ===============================================================================
    # plotters
    # ===============================================================================

    def _plot_aux(self, vk, po, pid):
        graph = self.graph
        # if '<sup>' in title or '<sub>' in title:
        #     self._set_ml_title(title, pid, 'y')
        # else:

        title = po.get_ytitle(vk)
        graph.set_y_title(title, plotid=pid)
        xs, ys, es, c39s, s39, vs = self._calculate_spectrum(value_key=vk)
        self.spectrum_values[pid] = xs, ys, es, c39s, s39, vs
        self.calculate_ylimits(po, s39, vs)

        s = self._add_plot(xs, ys, es, pid, po)
        return s

    def _plot_age_spectrum(self, po, plot, pid):
        graph = self.graph
        opt = self.options
        op = opt

        xs, ys, es, c39s, s39, vs = self._calculate_spectrum()
        self.spectrum_values[pid] = xs, ys, es, c39s, s39, vs
        self.xs = c39s

        ref = self.analyses[0]
        au = ref.arar_constants.age_units
        graph.set_y_title("Apparent Age ({})".format(au), plotid=pid)

        grp = opt.get_group(self.group_id)

        ag = self.analysis_group
        ag.integrated_include_omitted = opt.integrated_include_omitted
        ag.include_j_error_in_plateau = opt.include_j_error_in_plateau
        ag.plateau_age_error_kind = opt.plateau_age_error_kind
        ag.plateau_nsteps = opt.pc_nsteps
        ag.plateau_gas_fraction = opt.pc_gas_fraction
        ag.age_error_kind = opt.weighted_age_error_kind
        ag.integrated_age_weighting = opt.integrated_age_weighting

        if grp.calculate_fixed_plateau:
            ag.fixed_step_low, ag.fixed_step_high = (
                grp.calculate_fixed_plateau_start,
                grp.calculate_fixed_plateau_end,
            )
        else:
            ag.fixed_step_low, ag.fixed_step_high = ("", "")

        ag.dirty = True

        pma = None
        plateau_age = ag.plateau_age
        selections = ag.get_omitted_by_tag(self.sorted_analyses)

        spec = self._add_plot(xs, ys, es, pid, po)

        if plateau_age:
            platbounds = ag.plateau_steps

            txt = self._make_plateau_text()
            overlay = self._add_plateau_overlay(
                spec, platbounds, plateau_age, ys[::2], es[::2], txt
            )

            pma = nominal_value(plateau_age)
            overlay.id = "bar_plateau"
            if overlay.id in po.overlay_positions:
                y = po.overlay_positions[overlay.id]
                overlay.y = y
                pma = y
        elif opt.display_weighted_bar:
            txt = self._make_weighted_mean_text()
            wa = ag.weighted_age
            overlay = self._add_plateau_overlay(
                spec, [0, len(ys) // 2 - 1], wa, ys[::2], es[::2], txt
            )
            overlay.selections = selections
            overlay.id = "bar_weighted"
            pma = nominal_value(wa)
            if overlay.id in po.overlay_positions:
                y = po.overlay_positions[overlay.id]
                overlay.y = y
                pma = y

        self.calculate_ylimits(po, s39, vs, pma)

        text = self._build_age_text()
        if text:
            self._add_age_label(
                plot,
                text,
                font=op.integrated_font,
                relative_position=self.group_id,
                color=spec.color,
            )
        self._add_info(graph, plot)

        return spec

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = [
                    "Ages {}{}{}".format(PLUSMINUS, self.options.nsigma, SIGMA),
                    "Error Env. {}{}{}".format(
                        PLUSMINUS, self.options.step_nsigma, SIGMA
                    ),
                ]

                if ts:
                    self._add_info_label(plot, ts)

    def _add_age_label(self, plot, text, font="modern 10", relative_position=0, **kw):

        o = RelativePlotLabel(
            component=plot,
            text=text,
            hjustify="center",
            vjustify="bottom",
            font=font,
            relative_position=relative_position,
            **kw
        )
        self.age_label = o
        plot.overlays.append(o)

    def _add_plot(self, xs, ys, es, plotid, po):
        ag = self.analysis_group

        plateau_age = ag.plateau_age
        platbounds = None
        if plateau_age:
            platbounds = ag.plateau_steps

        graph = self.graph

        group = self.options.get_group(self.group_id)

        ds, p = graph.new_series(
            xs, ys, color=group.line_color, value_scale=po.scale, plotid=plotid
        )

        ls = group.center_line_style
        if not ls == "No Line":
            ds.line_style = ls
            ds.line_width = group.center_line_width
        else:
            ds.line_width = 0

        ds.value_mapper.fill_value = 1e-20
        ds.index.on_trait_change(self.update_graph_metadata, "metadata_changed")

        ds.index.sort_order = "ascending"
        ns = self.options.step_nsigma
        sp = SpectrumTool(
            component=ds, cumulative39s=xs, nsigma=ns, analyses=self.analyses
        )

        ov = SpectrumInspectorOverlay(tool=sp, component=ds)
        ds.tools.append(sp)
        ds.overlays.append(ov)

        # provide 1s errors use nsigma to control display
        ds.errors = es
        if po.y_error:
            sp = SpectrumErrorOverlay(
                component=ds,
                use_user_color=True,
                user_color=group.color,
                alpha=group.alpha,
                use_fill=group.use_fill,
                nsigma=ns,
                platbounds=platbounds,
                dim_non_plateau=self.options.dim_non_plateau,
            )
            ds.underlays.append(sp)

        omit = self.analysis_group.get_omitted_by_tag(self.sorted_analyses)
        sp.selections = omit

        self._set_renderer_selection((ds,), omit)

        self.spectrum_overlays.append(sp)
        if po.show_labels:
            grp = self.options.get_group(self.group_id)
            lo = SpectrumLabelOverlay(
                component=ds,
                nsigma=ns,
                sorted_analyses=self.sorted_analyses,
                use_user_color=True,
                user_color=grp.line_color,
                font=self.options.label_font,
                display_extract_value=self.options.display_extract_value,
                display_step=self.options.display_step,
            )

            ds.underlays.append(lo)

        return ds

    # ===============================================================================
    # overlays
    # ===============================================================================
    def _add_plateau_overlay(self, lp, bounds, plateau_age, ages, age_errors, info_txt):
        opt = self.options

        group = self.options.get_group(self.group_id)

        ov = PlateauOverlay(
            component=lp,
            plateau_bounds=bounds,
            cumulative39s=hstack(([0], self.xs)),
            info_txt=info_txt,
            ages=ages,
            age_errors=age_errors,
            line_width=group.line_width,
            line_color=group.line_color,
            extend_end_caps=opt.extend_plateau_end_caps,
            label_visible=opt.display_plateau_info,
            label_font=opt.plateau_font,
            arrow_visible=opt.plateau_arrow_visible,
            y=nominal_value(plateau_age),
        )

        lp.overlays.append(ov)
        tool = PlateauTool(component=ov)
        lp.tools.append(tool)
        ov.on_trait_change(self._handle_plateau_overlay_move, "position[]")
        self.plateau_overlay = ov
        return ov

    def _handle_plateau_overlay_move(self, obj, name, old, new):
        self._handle_overlay_move(obj, name, old, float(new[0]))

    # def update_index_mapper(self, gid, obj, name, old, new):
    # if new is True:
    # self._update_graph_metadata(gid, None, name, old, new)

    def update_graph_metadata(self, obj, name, old, new):
        # print 'update graph metadata, {} {} {} {}'.format(obj, name, old, new)
        sel = obj.metadata["selections"]

        sel1 = self._filter_metadata_changes(obj, self.sorted_analyses)

        for sp in self.spectrum_overlays:
            sp.selections = sel

        ag = self.analysis_group
        ag.dirty = True

        if self.age_label:
            # text = self._build_integrated_age_label(ag.integrated_age, ag.nanalyses)
            text = self._build_age_text()
            self.age_label.text = text

        if self.plateau_overlay:
            self.plateau_overlay.selections = sel
            if ag.plateau_age:
                self.plateau_overlay.plateau_bounds = ag.plateau_steps
                text = self._make_plateau_text()
            else:
                self.plateau_overlay.plateau_bounds = [0, len(self.analyses) - 1]
                text = self._make_weighted_mean_text()

            self.plateau_overlay.info_txt = text

        self.graph.plotcontainer.invalidate_and_redraw()
        self.recalculate_event = True

    # ===============================================================================
    # utils
    # ===============================================================================
    def _analysis_group_hook(self, ag):
        ag.set_isochron_trapped(
            self.options.use_isochron_trapped,
            self.options.include_isochron_trapped_error,
        )

    def _get_age_errors(self, ans):
        ages = [(nominal_value(ai), std_dev(ai)) for ai in ans]

        return array(ages).T

    def _calculate_spectrum(
        self, excludes=None, group_id=0, index_key="k39", value_key="uage"
    ):

        if excludes is None:
            excludes = []

        analyses = self.sorted_analyses
        values = [a.get_value(value_key) for a in analyses]
        ar39s = [nominal_value(a.get_computed_value(index_key)) for a in analyses]

        xs = []
        ys = []
        es = []
        sar = sum(ar39s)
        prev = 0
        c39s = []
        # steps = []
        for i, (aa, ar) in enumerate(zip(values, ar39s)):
            if isinstance(aa, tuple):
                ai, ei = aa
            else:
                if aa is None:
                    ai, ei = 0, 0
                else:
                    ai, ei = nominal_value(aa), std_dev(aa)

            xs.append(prev)

            if i in excludes:
                ei = 0
                ai = ys[-1]

            ys.append(ai)
            es.append(ei)
            try:
                s = 100 * ar / sar + prev
            except ZeroDivisionError:
                s = 0
            c39s.append(s)
            xs.append(s)
            ys.append(ai)
            es.append(ei)
            prev = s

        return array(xs), array(ys), array(es), array(c39s), array(ar39s), array(values)

    def _calc_error(self, we, mswd):
        ec = self.options.error_calc_method
        n = self.options.nsigma
        a = 1
        if ec == MSEM and mswd > 1:
            a = mswd**0.5
        return we * a * n

    # ===============================================================================
    # labels
    # ===============================================================================
    def _make_plateau_text(self):
        ag = self.analysis_group
        plateau_age = ag.plateau_age
        mswd_args = ag.get_plateau_mswd_tuple()
        plateau_mswd, valid_mswd, nsteps, pvalue = mswd_args

        op = self.options
        e = plateau_age.std_dev * op.nsigma
        text = self._build_label_text(
            nominal_value(plateau_age),
            e,
            nsteps,
            display_mswd=op.include_plateau_mswd,
            display_n=op.include_plateau_n,
            mswd_args=mswd_args,
            mswd_sig_figs=op.mswd_sig_figs,
            sig_figs=op.plateau_sig_figs,
        )

        sample = ag.sample
        identifier = ag.identifier
        fixed = ""
        fixed_steps = ag.fixed_steps
        if fixed_steps:
            if fixed_steps[0] or fixed_steps[1]:
                fixed = "Fixed ({}-{})".format(*fixed_steps)

        text = "{}Plateau= {}".format(fixed, text)

        if op.include_plateau_sample:
            if op.include_plateau_identifier:
                text = "{}({}) {}".format(sample, identifier, text)
            else:
                text = "{} {}".format(sample, text)
        elif op.include_plateau_identifier:
            text = "{} {}".format(identifier, text)

        return text

    def _make_weighted_mean_text(self):
        ag = self.analysis_group
        op = self.options

        a = ag.weighted_age
        n = ag.nanalyses
        mswd_args = ag.get_mswd_tuple()

        text = self._build_label_text(
            nominal_value(a),
            std_dev(a) * op.nsigma,
            n,
            display_mswd=op.include_age_mswd,
            display_n=op.include_age_n,
            mswd_args=mswd_args,
            mswd_sig_figs=op.mswd_sig_figs,
            sig_figs=op.weighted_mean_sig_figs,
        )
        text = "Weighted Mean= {}".format(text)
        return text

    def _make_integrated_text(self):
        ag = self.analysis_group
        tga = ag.integrated_age
        if ag.integrated_include_omitted:
            n = len(ag.analyses)
        else:
            n = ag.nanalyses
        text = self._build_integrated_age_label(tga, n)
        return text

    def _build_age_text(self):
        op = self.options
        if op.display_integrated_info or op.display_weighted_mean_info:
            text = ""
            if op.display_integrated_info:
                text = self._make_integrated_text()
            if op.display_weighted_mean_info:
                wmtext = self._make_weighted_mean_text()
                if text:
                    text = "{}    {}".format(text, wmtext)
                else:
                    text = wmtext
            return text

    def _build_integrated_age_label(self, tga, n):
        txt = "NaN"
        if not isnan(nominal_value(tga)):
            age, error = nominal_value(tga.nominal_value), std_dev(tga)

            error *= self.options.nsigma
            txt = self._build_label_text(
                age,
                error,
                n,
                display_n=self.options.include_age_n,
                sig_figs=self.options.integrated_sig_figs,
            )

        return "Integrated Age= {}".format(txt)


# ============= EOF =============================================
