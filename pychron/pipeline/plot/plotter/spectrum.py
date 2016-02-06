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
from traits.api import Array, List, Instance
# ============= standard library imports ========================
from math import isnan
from numpy import hstack, array
# ============= local library imports  ==========================
from uncertainties import nominal_value
from pychron.pipeline.plot.flow_label import FlowPlotLabel
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure
# from pychron.pipeline.plot import FlowPlotLabel
from pychron.pipeline.plot.overlays.label_overlay import SpectrumLabelOverlay, IntegratedPlotLabel
from pychron.pipeline.plot.overlays.spectrum import SpectrumTool, \
    SpectrumErrorOverlay, PlateauTool, PlateauOverlay, SpectrumInspectorOverlay
from pychron.pychron_constants import PLUSMINUS, SIGMA


class Spectrum(BaseArArFigure):
    xs = Array
    _omit_key = 'omit_spec'

    _analysis_group_klass = StepHeatAnalysisGroup
    spectrum_overlays = List
    plateau_overlay = Instance(PlateauOverlay)
    integrated_label = None

    def plot(self, plots, legend=None):
        """
            plot data on plots
        """

        graph = self.graph

        ag = self.analysis_group

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            plot = getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)
            if legend and po.plot_name == 'age_spectrum':
                ident = ag.identifier
                sample = ag.sample

                key = self.options.make_legend_key(ident, sample)
                if key in legend.plots:
                    ident = '{}-{:02d}'.format(ident, ag.aliquot)
                    key = self.options.make_legend_key(ident, sample)

                legend.plots[key] = plot

        # self.graph.set_x_title('Cumulative %39ArK', plotid=0)
        # self.set_x_title('Cumulative %<sup>39</sup>Ar<sub>K</sub>')
        self._set_ml_title('Cumulative %<sup>39</sup>Ar<sub>K</sub>', 0, 'x')

    def max_x(self, attr):
        return max([ai.nominal_value for ai in self._unpack_attr(attr)])

    def min_x(self, attr):
        return min([ai.nominal_value for ai in self._unpack_attr(attr)])

    def mean_x(self, *args):
        return 50

    # ===============================================================================
    # plotters
    # ===============================================================================

    def _plot_aux(self, title, vk, ys, po, plot, pid, es=None, **kw):
        graph = self.graph
        if '<sup>' in title or '<sub>' in title:
            self._set_ml_title(title, pid, 'y')
        else:
            graph.set_y_title(title, plotid=pid)

        xs, ys, es, c39s, s39, vs = self._calculate_spectrum(value_key=vk)
        self.calculate_ylimits(po, s39, vs)

        s = self._add_plot(xs, ys, es, pid, po)
        return s

    def _plot_age_spectrum(self, po, plot, pid):
        graph = self.graph
        op = self.options

        xs, ys, es, c39s, s39, vs = self._calculate_spectrum()

        self.xs = c39s
        ref = self.analyses[0]
        au = ref.arar_constants.age_units
        graph.set_y_title('Apparent Age ({})'.format(au), plotid=pid)

        grp = self.options.get_group(self.group_id)

        spec = self._add_plot(xs, ys, es, pid, po)
        ls = grp.center_line_style
        if not ls == 'No Line':
            spec.line_style = ls
            spec.line_width = grp.center_line_width
        else:
            spec.line_width = 0

        ag = self.analysis_group
        ag.include_j_error_in_plateau = self.options.include_j_error_in_plateau
        ag.plateau_age_error_kind = self.options.plateau_age_error_kind
        ag.pc_nsteps = self.options.pc_nsteps
        ag.pc_gas_fraction = self.options.pc_gas_fraction

        if grp.calculate_fixed_plateau:
            ag.calculate_fixed_plateau_steps = grp.calculate_fixed_plateau_start, grp.calculate_fixed_plateau_end
        else:
            ag.calculate_fixed_plateau_steps = tuple()

        pma = None
        plateau_age = ag.plateau_age
        if plateau_age:
            platbounds = ag.plateau_steps

            txt = self._make_plateau_text()
            overlay = self._add_plateau_overlay(spec, platbounds, plateau_age,
                                                ys[::2], es[::2],
                                                txt)

            selections = self._get_omitted_by_tag(self.sorted_analyses)
            overlay.selections = selections
            pma = plateau_age.nominal_value
            overlay.id = 'plateau'
            if overlay.id in po.overlay_positions:
                y = po.overlay_positions[overlay.id]
                overlay.y = y
                pma = y

        self.calculate_ylimits(po, s39, vs, pma)

        if op.display_integrated_info:
            text = self._make_integrated_text()
            # fs = op.integrated_font_size
            # if not fs:
            #     fs = 10

            self._add_integrated_label(plot,
                                       text,
                                       # font='modern {}'.format(fs),
                                       font=op.integrated_font,
                                       relative_position=self.group_id,
                                       color=spec.color)

            # label.id='integrated'
            # if label.id in po.overlay_positions:
            # label.label_position=po.overlay_positions[label.id]

        self._add_info(graph, plot)

        return spec

    def calculate_ylimits(self, po, s39, vs, pma=None):
        ps = s39 / s39.sum()
        ps = ps > 0.01
        vs = vs[ps]

        # filter ys,es if 39Ar < 1% of total
        try:
            vs, es = zip(*[(vi.nominal_value, vi.std_dev) for vi in vs])
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

        if not po.has_ylimits():
            if po.calculated_ymin is None:
                po.calculated_ymin = _mi
            else:
                po.calculated_ymin = min(po.calculated_ymin, _mi)

            if po.calculated_ymax is None:
                po.calculated_ymax = _ma
            else:
                po.calculated_ymax = max(po.calculated_ymax, _ma)

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = [u'Age {}{}{}'.format(PLUSMINUS, self.options.nsigma, SIGMA),
                      u'Error Env. {}{}{}'.format(PLUSMINUS, self.options.step_nsigma, SIGMA)]

                if ts:
                    pl = FlowPlotLabel(text='\n'.join(ts),
                                       overlay_position='inside top',
                                       hjustify='left',
                                       font=self.options.error_info_font,
                                       component=plot)
                    plot.overlays.append(pl)

    def _add_integrated_label(self, plot, text, font='modern 10', relative_position=0, **kw):

        o = IntegratedPlotLabel(component=plot, text=text,
                                hjustify='center', vjustify='bottom',
                                font=font,
                                relative_position=relative_position, **kw)
        self.integrated_label = o
        plot.overlays.append(o)

    def _add_plot(self, xs, ys, es, plotid, po):
        graph = self.graph

        group = self.options.get_group(self.group_id)

        ds, p = graph.new_series(xs, ys,
                                 color=group.line_color,
                                 value_scale=po.scale,
                                 plotid=plotid)

        ds.index.on_trait_change(self._update_graph_metadata, 'metadata_changed')

        ds.index.sort_order = 'ascending'
        ns = self.options.step_nsigma
        sp = SpectrumTool(component=ds,
                          cumulative39s=self.xs,
                          nsigma=ns,
                          analyses=self.analyses)

        ov = SpectrumInspectorOverlay(tool=sp, component=ds)
        ds.tools.append(sp)
        ds.overlays.append(ov)

        # provide 1s errors use nsigma to control display
        ds.errors = es
        if po.y_error:
            sp = SpectrumErrorOverlay(component=ds,
                                      use_user_color=True,
                                      user_color=group.color,
                                      alpha=group.alpha,
                                      use_fill=group.use_fill,
                                      nsigma=ns)
            ds.underlays.append(sp)

        omit = self._get_omitted_by_tag(self.sorted_analyses)
        sp.selections = omit

        self._set_renderer_selection((ds,), omit)

        self.spectrum_overlays.append(sp)
        if po.show_labels:
            grp = self.options.get_group(self.group_id)
            lo = SpectrumLabelOverlay(component=ds,
                                      nsigma=ns,
                                      sorted_analyses=self.sorted_analyses,
                                      use_user_color=True,
                                      user_color=grp.line_color,
                                      font=self.options.label_font,
                                      display_extract_value=self.options.display_extract_value,
                                      display_step=self.options.display_step)

            ds.underlays.append(lo)
        return ds

    # ===============================================================================
    # overlays
    # ===============================================================================
    def _add_plateau_overlay(self, lp, bounds, plateau_age, ages, age_errors, info_txt):
        opt = self.options

        # color = opt.get_group_color(self.group_id)
        # line_width = option.get_group(self.group_id)
        group = self.options.get_group(self.group_id)

        ov = PlateauOverlay(component=lp, plateau_bounds=bounds,
                            cumulative39s=hstack(([0], self.xs)),
                            info_txt=info_txt,
                            id='plateau',
                            ages=ages,
                            age_errors=age_errors,

                            line_width=group.line_width,
                            line_color=group.line_color,
                            # line_width=opt.plateau_line_width,
                            # line_color=opt.plateau_line_color if opt.user_plateau_line_color else lp.color,
                            # line_color=color,

                            extend_end_caps=opt.extend_plateau_end_caps,
                            label_visible=opt.display_plateau_info,
                            label_font=opt.plateau_font,
                            # label_font_size=opt.plateau_font_size,
                            arrow_visible=opt.plateau_arrow_visible,
                            # label_offset=plateau_age.std_dev*self.options.step_nsigma,
                            # y=plateau_age.nominal_value * 1.25)
                            y=nominal_value(plateau_age))

        # lp.underlays.append(ov)
        lp.overlays.append(ov)
        tool = PlateauTool(component=ov)
        lp.tools.append(tool)
        # plateau_label:[x, y
        ov.on_trait_change(self._handle_plateau_overlay_move, 'position[]')
        self.plateau_overlay = ov
        return ov

    def _handle_plateau_overlay_move(self, obj, name, old, new):
        self._handle_overlay_move(obj, name, old, float(new[0]))

    # def update_index_mapper(self, gid, obj, name, old, new):
    # if new is True:
    # self._update_graph_metadata(gid, None, name, old, new)

    def _update_graph_metadata(self, obj, name, old, new):
        # print 'update graph metadata, {} {} {} {}'.format(obj, name, old, new)
        sel = obj.metadata['selections']

        sel1 = self._filter_metadata_changes(obj, self.sorted_analyses)
        # print sel, sel1

        for sp in self.spectrum_overlays:
            sp.selections = sel

        if self.plateau_overlay:
            self.plateau_overlay.selections = sel

        ag = self.analysis_group
        ag.dirty = True

        text = self._build_integrated_age_label(ag.integrated_age, ag.nanalyses)
        self.integrated_label.text = text

        if ag.plateau_age and self.plateau_overlay:
            text = self._make_plateau_text()
            self.plateau_overlay.info_txt = text

        self.graph.plotcontainer.invalidate_and_redraw()
        self.refresh_unknowns_table = True

    # ===============================================================================
    # utils
    # ===============================================================================
    def _make_plateau_text(self):
        ag = self.analysis_group
        plateau_age = ag.plateau_age
        plateau_mswd, valid_mswd, nsteps = ag.get_plateau_mswd_tuple()

        e = plateau_age.std_dev * self.options.nsigma
        text = self._build_label_text(nominal_value(plateau_age), e, nsteps,
                                      mswd_args=(plateau_mswd, valid_mswd, nsteps),
                                      sig_figs=self.options.plateau_sig_figs)

        sample = self.analysis_group.sample
        identifier = self.analysis_group.identifier

        if self.options.include_plateau_sample:
            if self.options.include_plateau_identifier:
                text = u'{}({}) {}'.format(sample, identifier, text)
            else:
                text = u'{} {}'.format(sample, text)
        elif self.options.include_plateau_identifier:
            text = u'{} {}'.format(identifier, text)

        return text

    def _make_integrated_text(self):
        ag = self.analysis_group
        tga = ag.integrated_age
        n = ag.nanalyses
        # mswd = ag.get_mswd_tuple()
        text = self._build_integrated_age_label(tga, n)
        return text

    def _get_age_errors(self, ans):
        ages, errors = zip(*[(ai.uage.nominal_value,
                              ai.uage.std_dev)
                             for ai in ans])
        return array(ages), array(errors)

    def _calculate_spectrum(self,
                            excludes=None,
                            group_id=0,
                            index_key='k39',
                            value_key='uage'):

        if excludes is None:
            excludes = []

        analyses = self.sorted_analyses
        values = [a.get_value(value_key) for a in analyses]
        # values = [ufloat(10, 0.1) for vi in values]
        ar39s = [a.get_computed_value(index_key).nominal_value for a in analyses]

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
                    ai, ei = aa.nominal_value, aa.std_dev

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
        if ec == 'SEM':
            a = 1
        elif ec == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
            a = 1
            if mswd > 1:
                a = mswd ** 0.5
        return we * a * n

    # ===============================================================================
    # labels
    # ===============================================================================
    def _build_integrated_age_label(self, tga, n):
        txt = 'NaN'
        if not isnan(nominal_value(tga)):
            age, error = tga.nominal_value, tga.std_dev

            error *= self.options.nsigma
            txt = self._build_label_text(age, error, n, sig_figs=self.options.integrated_sig_figs)

        return u'Integrated Age= {}'.format(txt)

# ============= EOF =============================================
