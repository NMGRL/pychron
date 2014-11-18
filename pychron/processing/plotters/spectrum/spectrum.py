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
from math import isnan

from traits.api import Array

#============= standard library imports ========================
from numpy import hstack, array
#============= local library imports  ==========================
from uncertainties import nominal_value
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.processing.plotters.arar_figure import BaseArArFigure
from pychron.processing.plotters.flow_label import FlowPlotLabel
from pychron.processing.plotters.sparse_ticks import SparseLogTicks, SparseTicks
from pychron.processing.plotters.spectrum.label_overlay import SpectrumLabelOverlay, IntegratedPlotLabel
from pychron.processing.plotters.spectrum.tools import SpectrumTool, \
    SpectrumErrorOverlay, PlateauTool, PlateauOverlay, SpectrumInspectorOverlay


class Spectrum(BaseArArFigure):
    xs = Array
    _omit_key = 'omit_spec'

    _analysis_group_klass = StepHeatAnalysisGroup

    def plot(self, plots):
        """
            plot data on plots
        """
        graph = self.graph

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            # #     plotobj.value_mapper.low_setting = po.ylimits[0]
            # #     plotobj.value_mapper.high_setting = po.ylimits[1]
            # plotobj.value_mapper.low_setting = 0
            # plotobj.value_mapper.high_setting = 33

            getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)
            # self.update_options_limits(pid)

        try:
            self.graph.set_x_title('Cumulative %39ArK')
            self.graph.set_x_limits(0, 100)
        except IndexError:
            pass

    def max_x(self, attr):
        return max([ai.nominal_value for ai in self._unpack_attr(attr)])

    def min_x(self, attr):
        return min([ai.nominal_value for ai in self._unpack_attr(attr)])

    def mean_x(self, *args):
        return 50

    #===============================================================================
    # plotters
    #===============================================================================
    def _plot_aux(self, title, vk, ys, po, plot, pid, es=None, **kw):
        graph = self.graph
        graph.set_y_title(title,
                          plotid=pid)

        xs, ys, es, _, _, _ = self._calculate_spectrum(value_key=vk)
        s = self._add_plot(xs, ys, es, pid, po)
        return s

    def _plot_age_spectrum(self, po, plot, pid):
        graph = self.graph
        op = self.options

        xs, ys, es, c39s, s39, vs = self._calculate_spectrum()
        self.xs = c39s
        ref = self.analyses[0]
        au = ref.arar_constants.age_units
        graph.set_y_title('Apparent Age ({})'.format(au))

        spec = self._add_plot(xs, ys, es, pid, po)
        spec.line_style = self.options.center_line_style

        #add inspector
        # sp=SpectrumInspector(component=spec)
        # spec.tools.append(sp)

        ag = self.analysis_group
        ag.include_j_error_in_plateau = self.options.include_j_error_in_plateau
        ag.plateau_age_error_kind = self.options.plateau_age_error_kind

        pma = None
        if ag.plateau_age:
            plateau_age = ag.plateau_age
            plateau_mswd, valid_mswd, nsteps = ag.get_plateau_mswd_tuple()
            platbounds = ag.plateau_steps

            e = plateau_age.std_dev * self.options.nsigma
            info_txt = self._build_label_text(plateau_age.nominal_value, e,
                                              plateau_mswd, valid_mswd, nsteps,
                                              sig_figs=self.options.plateau_sig_figs)

            overlay = self._add_plateau_overlay(spec, platbounds, plateau_age,
                                                ys[::2], es[::2],
                                                info_txt)
            pma = plateau_age.nominal_value * 1.25
            overlay.id = 'plateau'
            if overlay.id in po.overlay_positions:
                y = po.overlay_positions[overlay.id]
                overlay.y = y
                pma = y


        # tga = self._calculate_total_gas_age(self.sorted_analyses)
        # print tga
        tga = ag.integrated_age
        mswd = ag.get_mswd_tuple()
        text = self._build_integrated_age_label(tga, *mswd)

        #filter ys,es if 39Ar < 1% of total
        ps = s39 / s39.sum()
        ps = ps > 0.01
        vs = vs[ps]
        try:
            vs, es = zip(*[(vi.nominal_value, vi.std_dev) for vi in vs])
            vs, es = array(vs), array(es)
            nes = es * op.step_nsigma
            yl = vs - nes
            yu = vs + nes

            _mi = min(yl)
            _ma = max(yu)
            if pma:
                _ma = max(pma, _ma)
        except ValueError:
            _mi=0
            _ma=1

        if op.display_integrated_info:
            fs = op.integrated_font_size
            if not fs:
                fs = 10

            self._add_integrated_label(plot,
                                       text,
                                       font='modern {}'.format(fs),
                                       relative_position=self.group_id,
                                       color=spec.color)

            # label.id='integrated'
            # if label.id in po.overlay_positions:
            #     label.label_position=po.overlay_positions[label.id]

        self._add_info(graph, plot)

        # print po.has_ylimits(),po.ylimits
        pad = '0.25'
        if po.has_ylimits():
            _mi, _ma = po.ylimits
            print 'using previous limits', _mi, _ma
            pad = None
        # print 'setting', _mi, _ma

        self.graph.set_y_limits(min_=_mi, max_=_ma, pad=pad, plotid=pid)
        # self._set_y_limits(_mi, _ma, pad=pad)

    def _add_info(self, g, plot):
        if self.group_id == 0:
            if self.options.show_info:
                ts = ['+/-{}s'.format(self.options.nsigma)]

                if ts:
                    pl = FlowPlotLabel(text='\n'.join(ts),
                                       overlay_position='inside top',
                                       hjustify='left',
                                       component=plot)
                    plot.overlays.append(pl)

    def _add_integrated_label(self, plot, text, font='modern 10', relative_position=0, **kw):

        o = IntegratedPlotLabel(component=plot, text=text,
                                hjustify='center', vjustify='bottom',
                                font=font,
                                relative_position=relative_position, **kw)

        plot.overlays.append(o)

    def _add_plot(self, xs, ys, es, plotid, po, value_scale='linear'):
        graph = self.graph

        ds, p = graph.new_series(xs, ys, plotid=plotid)

        #         u = lambda a, b, c, d: self.update_graph_metadata(ds, group_id, a, b, c, d)
        #         ds.index.on_trait_change(u, 'metadata_changed')

        ds.index.sort_order = 'ascending'
        #         ds.index.on_trait_change(self._update_graph, 'metadata_changed')

        #        sp = SpectrumTool(ds, spectrum=self, group_id=group_id)
        sp = SpectrumTool(component=ds, cumulative39s=self.xs)
        ov = SpectrumInspectorOverlay(tool=sp, component=ds)
        ds.tools.append(sp)
        ds.overlays.append(ov)

        # provide 1s errors use nsigma to control display
        ds.errors = es

        ns = self.options.step_nsigma
        a = self.options.envelope_alpha * 0.01

        sp = SpectrumErrorOverlay(component=ds,
                                  spectrum=self,
                                  alpha=max(min(1.0, a), 0.0),
                                  nsigma=ns)
        ds.underlays.append(sp)

        if po.show_labels:
            lo = SpectrumLabelOverlay(component=ds,
                                      nsigma=ns,
                                      spectrum=self,
                                      font_size=self.options.step_label_font_size,
                                      display_extract_value=self.options.display_extract_value,
                                      display_step=self.options.display_step)

            ds.underlays.append(lo)

        if value_scale == 'log':
            p.value_axis.tick_generator = SparseLogTicks()
        else:
            p.value_axis.tick_generator = SparseTicks()
        return ds

    #===============================================================================
    # overlays
    #===============================================================================
    def _add_plateau_overlay(self, lp, bounds, plateau_age, ages, age_errors, info_txt):
        ov = PlateauOverlay(component=lp, plateau_bounds=bounds,
                            cumulative39s=hstack(([0], self.xs)),
                            info_txt=info_txt,
                            id='plateau',
                            ages=ages,
                            age_errors=age_errors,
                            line_width=self.options.plateau_line_width,
                            line_color=self.options.plateau_line_color,
                            extend_end_caps=self.options.extend_plateau_end_caps,
                            label_visible=self.options.display_plateau_info,
                            label_font_size=self.options.plateau_font_size,

                            # label_offset=plateau_age.std_dev*self.options.step_nsigma,
                            y=plateau_age.nominal_value * 1.25)

        lp.underlays.append(ov)

        tool = PlateauTool(component=ov)
        lp.tools.append(tool)
        #plateau_label:[x, y
        ov.on_trait_change(self._handle_plateau_overlay_move, 'position[]')

        return ov

    def _handle_plateau_overlay_move(self, obj, name, old, new):
        self._handle_overlay_move(obj, name, old, float(new[0]))

    def update_index_mapper(self, gid, obj, name, old, new):
        if new is True:
            self.update_graph_metadata(gid, None, name, old, new)

    def update_graph_metadata(self, group_id, obj, name, old, new):
        pass

    #===============================================================================
    # utils
    #===============================================================================
    def _get_age_errors(self, ans):
        ages, errors = zip(*[(ai.uage.nominal_value,
                              ai.uage.std_dev)
                             for ai in ans])
        return array(ages), array(errors)

    def _calculate_spectrum(self,
                            excludes=None,
                            group_id=0,
                            index_key='k39',
                            value_key='uage_wo_j_err'):

        if excludes is None:
            excludes = []

        analyses = self.sorted_analyses

        #values = [getattr(a, value_key) for a in analyses]
        values = [a.get_value(value_key) for a in analyses]
        ar39s = [a.get_computed_value(index_key).nominal_value for a in analyses]

        xs = []
        ys = []
        es = []
        sar = sum(ar39s)
        prev = 0
        c39s = []
        #        steps = []
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
                s=0
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

    #===============================================================================
    # labels
    #===============================================================================
    def _build_integrated_age_label(self, tga, *args):
        txt='NaN'
        if not isnan(nominal_value(tga)):
            age, error = tga.nominal_value, tga.std_dev
            error *= self.options.nsigma
            txt = self._build_label_text(age, error, *args, sig_figs=2)

        return 'Integrated Age= {}'.format(txt)
        #============= EOF =============================================
        # def _get_plateau(self, analyses, exclude=None):
        # if exclude is None:
        #     exclude = []
        #
        # ages, errors = self._get_age_errors(self.sorted_analyses)
        # k39s = [a.computed['k39'].nominal_value for a in self.sorted_analyses]
        #
        # # provide 1s errors
        # platbounds = find_plateaus(ages, errors, k39s, overlap_sigma=2, exclude=exclude)
        # n = 0
        # if platbounds is not None and len(platbounds):
        #     n = platbounds[1] - platbounds[0] + 1
        #
        # if n > 1:
        #     ans = []
        #
        #     for j, ai in enumerate(analyses):
        #         if j not in exclude and platbounds[0] <= j <= platbounds[1]:
        #             ans.append(ai)
        #             #            ans=[ai for (j,ai) in analyses if]
        #             #            ans = analyses[platbounds[0]:platbounds[1]]
        #
        #     ages, errors = self._get_age_errors(ans)
        #     mswd, valid, n = self._get_mswd(ages, errors)
        #     plateau_age = self._calculate_total_gas_age(ans)
        #     return plateau_age, platbounds, mswd, valid, n
        # else:
        #     return 0, array([0, 0]), 0, 0, 0

        # def _calculate_total_gas_age(self, analyses):
        #     """
        #         sum the corrected rad40 and k39 values
        #
        #         not necessarily the same as isotopic recombination
        #
        #     """
        #     rad40, k39 = zip(*[(a.get_computed_value('rad40'),
        #                         a.get_computed_value('k39')) for a in analyses])
        #
        #     rad40 = sum(rad40)
        #     k39 = sum(k39)
        #
        #     j = a.j
        #     return age_equation(rad40 / k39, j, a.arar_constants)
        #
        #     # rad40, k39 = zip(*[(a.computed['rad40'], a.computed['k39']) for a in analyses])
        #     # rad40 = sum(rad40)
        #     # k39 = sum(k39)
        #     #
        #     # j = a.j
        #     # return age_equation(rad40 / k39, j, arar_constants=a.arar_constants)
        # def _add_aux_plot(self, ys, title, vk, pid, po, **kw):
        # graph = self.graph
        # graph.set_y_title(title,
        #                   plotid=pid)
        #
        # xs, ys, es, _ = self._calculate_spectrum(value_key=vk)
        # s = self._add_plot(xs, ys, es, pid, po, **kw)
        # return s

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

        #         sorted_ans = self.sorted_analyses
        #         if obj:
        #             hover = obj.metadata.get('hover')
        #             if hover:
        #                 hoverid = hover[0]
        #                 try:
        #                     self.selected_analysis = sorted_ans[hoverid]
        #                 except IndexError, e:
        #                     print 'asaaaaa', e
        #                     return
        #             else:
        #                 self.selected_analysis = None
        #
        #             sel = obj.metadata.get('selections', [])
        #
        #             if sel:
        #                 obj.was_selected = True
        #                 self._rebuild_fig(sel)
        #             elif hasattr(obj, 'was_selected'):
        #                 if obj.was_selected:
        #                     self._rebuild_spec(sel)
        #
        #                 obj.was_selected = False
        #
        #             # set the temp_status for all the analyses
        #             for i, a in enumerate(sorted_ans):
        #                 a.temp_status = 1 if i in sel else 0
        #         else:
        #             sel = [i for i, a in enumerate(sorted_ans)
        #                     if a.temp_status or a.status]
        #
        #             self._rebuild_spec(sel)
        #     def _rebuild_spec(self, sel):
        #         pass