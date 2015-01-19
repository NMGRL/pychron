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
import time

from chaco.legend import Legend
from traits.api import Str

#============= standard library imports ========================
from numpy import where
#============= local library imports  ==========================
from uncertainties import std_dev, nominal_value
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.core.regression.wls_regressor import WeightedPolynomialRegressor
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.processing.tasks.analysis_edit.interpolation_editor import InterpolationEditor



class BlanksEditor(InterpolationEditor):
    name = Str
    pickle_path = 'blank_fits'

    def load_fits(self, ref_ans):
        keys = ref_ans.isotope_keys[:]
        fits = [(ref_ans.isotopes[ki].blank.fit,
                 ref_ans.isotopes[ki].blank.error_type,
                 ref_ans.isotopes[ki].blank.filter_outliers_dict) for ki in keys]

        self.tool.load_fits(keys, fits)

    def do_fit(self, ans):
        pass

    def save(self, progress=None):
        if not any([si.save for si in self.tool.fits]):
            return

        db = self.processor.db
        with db.session_ctx():
            cname = 'blanks'
            self.info('Attempting to save corrections to database')

            n = len(self.analyses)
            if n > 1:
                if progress is None:
                    progress = self.processor.open_progress(n*len(self.tool.fits))
                else:
                    progress.increase_max(n+1)

            refs = self._clean_references()
            set_id = self.processor.add_predictor_set(refs, 'blanks')

            for si in self.tool.fits:
                if si.use:
                    ys,es = self._get_reference_values(si.name, ans=refs)
                    xs = [ri.timestamp for ri in refs]

                    reg = self._get_regressor(si.fit, si.error_type, xs, ys, es)
                    self.set_interpolated_values(si.name, reg, None)

            ans = self.analyses
            ms = db.get_analyses_uuid([unk.uuid for unk in ans], analysis_only=True)

            args = [mi.id for mi in ms]
            sid = self.processor.unique_id(args, time.time())

            fit_summary = ','.join(['{}{}'.format(si.name,si.fit)
                                    for si in self.tool.fits if si.use])

            dbaction = db.add_proc_action('Set Blanks for {} to {}. Fits={}'.format(ans[0].record_id,
                                                                                    ans[-1].record_id,
                                                                                    fit_summary),
                                          session=sid)
            for unk, meas_analysis in zip(ans, ms):
                if progress:
                    progress.change_message('Saving blanks for {}'.format(unk.record_id))

                # meas_analysis = db.get_analysis_uuid(unk.uuid)

                histories = getattr(meas_analysis, '{}_histories'.format(cname))
                phistory = histories[-1] if histories else None

                history = self.processor.add_history(meas_analysis, cname)
                history.action = dbaction

                for si in self.tool.fits:
                    if not si.fit:
                        msg = 'Skipping {} {}'.format(unk.record_id, si.name)
                        self.debug(msg)
                        if progress:
                            progress.change_message(msg)

                    if not si.use:
                        msg = 'Using previous value {} {}'.format(unk.record_id, si.name)
                        self.debug(msg)
                        if progress:
                            progress.change_message(msg)
                        self.processor.apply_fixed_value_correction(phistory, history, si, cname)
                    else:
                        msg ='Saving {} {}'.format(unk.record_id, si.name)
                        self.debug(msg)
                        if progress:
                            progress.change_message(msg)

                        dbblank = self.processor.apply_correction(history, unk, si, set_id, cname)
                        self.processor.add_predictor_valueset(refs, ys, es, dbblank)

                        if si.fit == 'preceding':
                            dbid = self._get_preceding_analysis(db, unk, refs)
                            if dbid:
                                dbblank.preceding_id = dbid.id

                                # unk.sync(meas_analysis)
                unk.sync_blanks(meas_analysis)
                unk.calculate_age(force=True)
                
            # if self.auto_plot:
            self.rebuild_graph()

            # fits = ','.join(('{} {}'.format(fi.name, fi.fit) for fi in self.tool.fits if fi.use))
            # self.processor.update_vcs_analyses(self.analyses,
            #                                    'Update blanks fits={}'.format(fits))

            if progress:
                progress.soft_close()

    def _get_regressor(self, fit, error_type, xs, ys, es):
        fit=fit.lower()
        if fit in ('linear','parabolic','cubic'):
            reg = WeightedPolynomialRegressor(fit=fit)

        elif fit in ['preceding', 'bracketing interpolate', 'bracketing average']:
            reg = InterpolationRegressor(kind=fit)
        elif fit =='weighted mean':
            reg = WeightedMeanRegressor()
        else:
            print 'fit {} not valid'.format(fit)
            raise NotImplementedError

        mi= min(xs)
        xs=[xi-mi for xi in xs]
        reg.trait_set(error_type=error_type,
                             xs=xs, ys=ys, yserr=es)
        reg.calculate()
        return reg

    def _get_preceding_analysis(self, db, unk, refs):
        xs = [ri.timestamp for ri in refs]
        try:
            ti = where(xs <= unk.timestamp)[0][-1]
        except IndexError:
            ti = 0

        return db.get_analysis_uuid(refs[ti].uuid)

    def _set_interpolated_values(self, iso, ans, p_uys, p_ues):
        for ui, v, e in zip(ans, p_uys, p_ues):
            if v is not None and e is not None:
                ui.set_temporary_blank(iso, v, e)

    def _get_current_values(self, iso, ans=None):
        if ans is None:
            ans = self.analyses

        return zip(*[self._get_isotope(ui, iso, 'blank')
                     for ui in ans])

    def _get_baseline_corrected(self, analysis, k):
        if k in analysis.isotopes:
            iso = analysis.isotopes[k]
            v = iso.get_baseline_corrected_value()
            return nominal_value(v), std_dev(v)
        else:
            return 0, 0

    def _get_reference_values(self, iso, ans=None):
        if ans is None:
            ans = self.references

        return zip(*[self._get_baseline_corrected(ui, iso)
                     for ui in ans])

    def _add_legend(self):
        # mapping = {'plot1': 'Blanks',
        #            'Unknowns-Current': 'Current',
        #            'Unknowns-predicted': 'Predicted'}
        plot = self.graph.plots[-1]
        ps = {}

        for k, v in plot.plots.items():
            if k == 'Unknowns-Current':
                ps['Current'] = v
            elif k.startswith('Unknowns-predicted'):
                ps['Predicted'] = v
            elif k.startswith('data') or k == 'plot1':
                ps['Blanks'] = v

        # print plot.plots.keys()
        # for k, v in plot.plots.items():
        #     for ki in mapping.keys():
        #         if k.startswith(ki):
        #             n = mapping[ki]
        #             ps[n] = v
        #             break
        #     else:
        #         if k in mapping:
        #             n = mapping[k]
        #             ps[n] = v

        l = Legend(plots=ps)
        plot.overlays.append(l)
        # plot.invalidate_and_redraw()

    def _graph_default(self):
        return StackedRegressionGraph(container_dict=dict(stack_order='top_to_bottom'))


        #============= EOF =============================================
        #     def _rebuild_graph(self):
        #         graph = self.graph
        #
        #         uxs = [ui.timestamp for ui in self._unknowns]
        #         rxs = [ui.timestamp for ui in self._references]
        #
        #         display_xs = asarray(map(convert_timestamp, rxs[:]))
        #
        #         start, end = self._get_start_end(rxs, uxs)
        #
        #         c_uxs = self.normalize(uxs, start)
        #         r_xs = self.normalize(rxs, start)
        #
        #         def get_isotope(ui, k, kind=None):
        #             if k in ui.isotopes:
        #                 v = ui.isotopes[k]
        #                 if kind is not None:
        #                     v = getattr(v, kind)
        #                 v = v.value, v.error
        #             else:
        #                 v = 0, 0
        #             return v
        #
        #         '''
        #             c_... current value
        #             r... reference value
        #             p_... predicted value
        #         '''
        #         set_x_flag = False
        #         i = 0
        #         gen = self._graph_generator()
        #         for i, fit in enumerate(gen):
        #             iso = fit.name
        #             set_x_flag = True
        #             fit = fit.fit.lower()
        #             c_uys, c_ues = None, None
        #
        #             if self._unknowns and self.show_current:
        #                 c_uys, c_ues = zip(*[get_isotope(ui, iso, 'blank')
        #                             for ui in self._unknowns
        #                             ])
        #
        #             r_ys, r_es = None, None
        #             if self._references:
        #                 r_ys, r_es = zip(*[get_isotope(ui, iso)
        #                             for ui in self._references
        #                             ])
        #
        #             p = graph.new_plot(
        #                                ytitle=iso,
        #                                xtitle='Time (hrs)',
        #                                padding=[80, 5, 5, 40],
        # #                                show_legend='ur' if i == 0 else False
        #                                )
        #             p.value_range.tight_bounds = False
        #
        #             if c_ues and c_uys:
        #                 # plot unknowns
        #                 graph.new_series(c_uxs, c_uys,
        #                                  yerror=c_ues,
        #                                  fit=False,
        #                                  type='scatter',
        #                                  plotid=i
        #                                  )
        #                 graph.set_series_label('Unknowns-Current', plotid=i)
        #
        #             if r_es and r_ys:
        #                 reg = None
        #                 # plot references
        #                 if fit in ['preceding', 'bracketing interpolate', 'bracketing average']:
        #                     reg = InterpolationRegressor(xs=r_xs,
        #                                                  ys=r_ys,
        #                                                  yserr=r_es,
        #                                                  kind=fit)
        #                     scatter, _p = graph.new_series(r_xs, r_ys,
        #                                  yerror=r_es,
        #                                  type='scatter',
        #                                  plotid=i,
        #                                  fit=False
        #                                  )
        #
        #                 else:
        #                     _p, scatter, l = graph.new_series(r_xs, r_ys,
        #                                        display_index=ArrayDataSource(data=display_xs),
        #                                        yerror=ArrayDataSource(data=r_es),
        #                                        fit=fit,
        #                                        plotid=i)
        #                     if hasattr(l, 'regressor'):
        #                         reg = l.regressor
        # #                    if fit.startswith('average'):
        # #                        reg2 = MeanRegressor(xs=r_xs, ys=r_ys, yserr=r_es)
        # #                    else:
        # #                        reg2 = OLSRegressor(xs=r_xs, ys=r_ys, yserr=r_es, fit=fit)
        #
        # #                p_uys = reg.predict(c_uxs)
        # #                p_ues = reg.predict_error(c_uxs)
        # #
        # #                for ui, v, e in zip(self._unknowns, p_uys, p_ues):
        # #                    ui.set_blank(iso, v, e)
        # #                        ui.blank.value = v
        # #                        ui.blank.error = e
        #                 if reg:
        #                     p_uys, p_ues = self._set_interpolated_values(iso, reg, c_uxs)
        #                     # display the predicted values
        #                     ss, _ = graph.new_series(c_uxs,
        #                                              p_uys,
        #                                              isotope=iso,
        #                                              yerror=ArrayDataSource(p_ues),
        #                                              fit=False,
        #                                              type='scatter',
        #                                              plotid=i,
        #                                              )
        #                     graph.set_series_label('Unknowns-predicted', plotid=i)
        #             i += 1
        #
        #         if set_x_flag:
        #             m = abs(end - start) / 3600.
        #             graph.set_x_limits(0, m, pad='0.1')
        #             graph.refresh()

        #def _make_references(self):
        #
        #    keys = set([ki for ui in self._references
        #                for ki in ui.isotope_keys])
        #    keys = sort_isotopes(keys)
        #    fits = ['linear', ] * len(keys)
        #
        #    self.tool.load_fits(keys, fits)

        #def load_fits(self, refiso):
        #pass
        #self.tool.load_fits(refiso.isotope_keys,
        #                    refiso.isotope_fits)