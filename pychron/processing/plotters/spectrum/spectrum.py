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
from traits.api import Array
#============= standard library imports ========================
from numpy import hstack, array
#============= local library imports  ==========================
from pychron.processing.plotters.arar_figure import BaseArArFigure
from pychron.processing.plotters.sparse_ticks import SparseLogTicks, SparseTicks
from pychron.processing.plotters.spectrum.label_overlay import SpectrumLabelOverlay
from pychron.processing.plotters.spectrum.tools import SpectrumTool, \
    SpectrumErrorOverlay, PlateauTool, PlateauOverlay
from pychron.processing.argon_calculations import find_plateaus, age_equation


class Spectrum(BaseArArFigure):

    xs = Array
    _omit_key = 'omit_spec'

    def plot(self, plots):
        """
            plot data on plots
        """
        graph = self.graph

        for pid, (plotobj, po) in enumerate(zip(graph.plots, plots)):
            getattr(self, '_plot_{}'.format(po.plot_name))(po, plotobj, pid)

        try:
            self.graph.set_x_title('Cumulative %39ArK')
        except IndexError:
            pass

    def max_x(self, attr):
        return max([ai.nominal_value for ai in self._unpack_attr(attr)])

    def min_x(self, attr):
        return min([ai.nominal_value for ai in self._unpack_attr(attr)])

    #===============================================================================
    # plotters
    #===============================================================================
    def _plot_aux(self, title, vk, ys, po, plot, pid, es=None):
        self._add_aux_plot(ys, title, vk, pid, po)

    def _plot_age_spectrum(self, po, plot, pid):
        graph = self.graph

        xs, ys, es, c39s = self._calculate_spectrum()
        self.xs = c39s
        ref = self.analyses[0]
        au = ref.arar_constants.age_units
        graph.set_y_title('Age ({})'.format(au))

        spec = self._add_plot(xs, ys, es, pid, po)

        args = self._get_plateau(self.sorted_analyses)
        if args:
            plateau_age, platbounds, plateau_mswd, valid_mswd, nplateau_steps = args

        # if not isinstance(plateau_age, int):
            info_txt=self._build_label_text(plateau_age.nominal_value, plateau_age.std_dev,
                                            plateau_mswd, valid_mswd, nplateau_steps)

            self._add_plateau_overlay(spec, platbounds, plateau_age, info_txt)

        tga = self._calculate_total_gas_age(self.sorted_analyses)

        text = self._build_integrated_age_label(tga, *self._get_mswd(ys[::2], es[::2]))

        ys, es = array(ys), array(es)
        ns = self.options.step_nsigma
        yl = (ys - es * ns)[::-1]
        yu = ys + es * ns

        miages = min(yl)
        maages = max(yu)

        dl = self._add_data_label(spec, text,
                                  (25, miages),
                                  font='modern 10',
                                  label_position='bottom right',
                                  append=False)

        self._set_y_limits(miages, maages, pad='0.1')

    #         d = lambda a, b, c, d: self.update_index_mapper(a, b, c, d)
    #         plot.index_mapper.on_trait_change(d, 'updated')

    def _add_plot(self, xs, ys, es, plotid, po, value_scale='linear'):
        graph = self.graph

        ds, p = graph.new_series(xs, ys, plotid=plotid)

        #         u = lambda a, b, c, d: self.update_graph_metadata(ds, group_id, a, b, c, d)
        #         ds.index.on_trait_change(u, 'metadata_changed')

        ds.index.sort_order = 'ascending'
        #         ds.index.on_trait_change(self._update_graph, 'metadata_changed')

        #        sp = SpectrumTool(ds, spectrum=self, group_id=group_id)
        sp = SpectrumTool(ds, cumulative39s=self.xs)
        ds.tools.append(sp)

        # provide 1s errors use nsigma to control display
        ds.errors = es

        ns = self.options.step_nsigma
        sp = SpectrumErrorOverlay(component=ds, spectrum=self,
                                  nsigma=ns)
        ds.overlays.append(sp)

        if po.show_labels:
            lo= SpectrumLabelOverlay(component=ds,
                                     nsigma=ns,
                                     spectrum=self,

                                     display_extract_value=self.options.display_extract_value,
                                     display_step=self.options.display_step)

            ds.overlays.append(lo)

        if value_scale == 'log':
            p.value_axis.tick_generator = SparseLogTicks()
        else:
            p.value_axis.tick_generator = SparseTicks()
        return ds

    #===============================================================================
    # overlays
    #===============================================================================
    def _add_plateau_overlay(self, lp, bounds, plateau_age, info_txt):
        ov = PlateauOverlay(component=lp, plateau_bounds=bounds,
                            cumulative39s=hstack(([0], self.xs)),
                            info_txt=info_txt,
                            label_visible=self.options.display_plateau_info,
                            label_offset=plateau_age.std_dev*self.options.step_nsigma,
                            y=plateau_age.nominal_value)

        lp.overlays.append(ov)

        tool = PlateauTool(component=ov)
        lp.tools.insert(0, tool)

    def update_index_mapper(self, gid, obj, name, old, new):
        if new is True:
            self.update_graph_metadata(gid, None, name, old, new)

    def update_graph_metadata(self, group_id, obj, name, old, new):
        pass

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

    #===============================================================================
    # utils
    #===============================================================================
    def _get_age_errors(self, ans):
        ages, errors = zip(*[(ai.uage.nominal_value,
                              ai.uage.std_dev)
                             for ai in ans])
        return array(ages), array(errors)

    def _get_plateau(self, analyses, exclude=None):
        if exclude is None:
            exclude = []

        ages, errors = self._get_age_errors(self.sorted_analyses)
        k39s = [a.computed['k39'].nominal_value for a in self.sorted_analyses]

        # provide 1s errors
        platbounds = find_plateaus(ages, errors, k39s, overlap_sigma=2, exclude=exclude)
        n = 0
        if platbounds is not None and len(platbounds):
            n = platbounds[1] - platbounds[0] + 1

        if n > 1:
            ans = []

            for j, ai in enumerate(analyses):
                if j not in exclude and platbounds[0] <= j <= platbounds[1]:
                    ans.append(ai)
                    #            ans=[ai for (j,ai) in analyses if]
                    #            ans = analyses[platbounds[0]:platbounds[1]]

            ages, errors = self._get_age_errors(ans)
            mswd, valid, n = self._get_mswd(ages, errors)
            plateau_age = self._calculate_total_gas_age(ans)
            return plateau_age, platbounds, mswd, valid, n
        # else:
        #     return 0, array([0, 0]), 0, 0, 0

    def _calculate_total_gas_age(self, analyses):
        """
            sum the corrected rad40 and k39 values

            not necessarily the same as isotopic recombination

        """

        rad40, k39 = zip(*[(a.computed['rad40'], a.computed['k39']) for a in analyses])
        rad40 = sum(rad40)
        k39 = sum(k39)

        j = a.j
        return age_equation(rad40 / k39, j, arar_constants=a.arar_constants)

    def _calculate_spectrum(self,
                            excludes=None,
                            group_id=0,
                            index_key='k39',
                            value_key='uage'):

        if excludes is None:
            excludes = []

        analyses = self.sorted_analyses

        #values = [getattr(a, value_key) for a in analyses]
        values = [a.get_value(value_key) for a in analyses]
        ar39s = [a.computed[index_key].nominal_value for a in analyses]

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
                ai, ei = aa.nominal_value, aa.std_dev

            xs.append(prev)

            if i in excludes:
                ei = 0
                ai = ys[-1]

            ys.append(ai)
            es.append(ei)

            s = 100 * ar / sar + prev
            c39s.append(s)
            xs.append(s)
            ys.append(ai)
            es.append(ei)
            prev = s

        return array(xs), array(ys), array(es), array(c39s)  # , array(ar39s), array(values)


    def _add_aux_plot(self, ys, title, vk, pid, po, **kw):
        graph = self.graph
        graph.set_y_title(title,
                          plotid=pid)

        xs, ys, es, _ = self._calculate_spectrum(value_key=vk)
        s = self._add_plot(xs, ys, es, pid, po, **kw)
        return s

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
        age, error = tga.nominal_value, tga.std_dev
        error *= self.options.nsigma
        txt = self._build_label_text(age, error, *args)
        return 'Integrated Age= {}'.format(txt)

#============= EOF =============================================
