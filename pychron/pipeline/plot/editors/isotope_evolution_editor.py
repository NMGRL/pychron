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
from traits.api import Event

# ============= standard library imports ========================
from numpy import polyfit

# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.pipeline.plot.models.iso_evo_model import IsoEvoModel
from pychron.pipeline.plot.editors.figure_editor import FigureEditor


def fits_equal(dbfit, fit, fod):
    """
    return True if fits are the same
    """
    same = False
    if dbfit.fit == fit:
        a = fod["filter_outliers"] == dbfit.filter_outliers
        b = fod["iterations"] == dbfit.filter_outlier_iterations
        c = fod["std_devs"] == dbfit.filter_outlier_std_devs
        return a and b and c

    return same


class IsoEvoGraph(Graph):
    _eq_visible_dict = None
    _eq_only_dict = None
    replot_needed = Event

    # def _get_selected_plotid(self):
    #     r = 0
    #     if self.selected_plot is not None:
    #         for ci in self.plotcontainer.components:
    #             for i, cii in enumerate(ci.components):
    #                 if cii == self.selected_plot:
    #                     r = i
    #                     break
    #                     # print ci, cii
    #                     # for gi in self.graphs:
    #                     # for pp in gi.plots:
    #                     # pp == self.selected_plot
    #                     #
    #                     # r = self.plots.index(self.selected_plot)
    #     # print 'get selected plotid', r, self.selected_plot
    #     return r

    def get_child_context_menu_actions(self):
        sid = self.selected_plotid
        # print 'get context', sid
        v = False
        try:
            v = self._eq_visible_dict[sid]
        except KeyError:
            pass
        except TypeError:
            self._eq_visible_dict = {sid: False}

        if v:
            a = self.action_factory("Hide Equilibration", "_hide_equilibration")
        else:
            a = self.action_factory("Show Equilibration", "_show_equilibration")

        v = False
        try:
            v = self._eq_only_dict[sid]
        except KeyError:
            pass
        except TypeError:
            self._eq_only_dict = {sid: False}

        if v:
            b = self.action_factory(
                "Hide Equilibration Only", "_hide_equilibration_only"
            )
        else:
            b = self.action_factory(
                "Show Equilibration Only", "_show_equilibration_only"
            )

        return [a, b]

    def _hide_equilibration(self):
        self._toggle_eq(False)

    def _show_equilibration(self):
        self._toggle_eq(True)

    def _toggle_eq(self, v):
        sid = self.selected_plotid
        try:
            self._eq_visible_dict[sid] = v
        except AttributeError:
            self._eq_visible_dict = {sid: v}
        self.replot_needed = True

    def _hide_equilibration_only(self):
        self._toggle_eq_only(False)

    def _show_equilibration_only(self):
        self._toggle_eq_only(True)

    def _toggle_eq_only(self, v):
        sid = self.selected_plotid
        try:
            self._eq_only_dict[sid] = v
        except AttributeError:
            self._eq_only_dict = {sid: v}
        self.replot_needed = True

    def set_dicts(self, d):
        self._eq_visible_dict, self._eq_only_dict = d

    def get_dicts(self):
        return self._eq_visible_dict, self._eq_only_dict

    def get_eq_visible(self, idx):
        try:
            return self._eq_visible_dict[idx]
        except (TypeError, KeyError):
            return False

    def get_eq_only_visible(self, idx):
        try:
            return self._eq_only_dict[idx]
        except (TypeError, KeyError):
            return False


class IsotopeEvolutionEditor(FigureEditor):
    # component = Any
    # tool = Instance(IsoEvoFitSelector)
    figure_model_klass = IsoEvoModel
    basename = "IsoEvo"

    # pickle_path = 'iso_fits'
    # unpack_peaktime = True
    # calculate_age = False

    # def _plot_baselines(self, add_tools, fd, fit, trunc, g, i, isok, unk):
    #     isok = isok[:-2]
    #     iso = unk.isotopes[isok]
    #     time_zero_offset = self.tool.time_zero_offset
    #     iso.baseline.time_zero_offset = time_zero_offset
    #     xs, ys = iso.baseline.offset_xs, iso.baseline.ys
    #
    #     g.new_series(xs, ys,
    #                  fit=fit.fit,
    #                  filter_outliers_dict=fd,
    #                  add_tools=add_tools,
    #                  plotid=i)
    #     return xs
    #
    # def _plot_ratio(self, add_tools, fd, fit, g, i, isok, trunc, unk):
    #     # correct for baseline when plotting ratios
    #     n, d = isok.split('/')
    #     niso, diso = unk.isotopes[n], unk.isotopes[d]
    #     nsniff, dsniff = niso.sniff, diso.sniff
    #     nbs, dbs = niso.baseline.value, diso.baseline.value
    #     if nsniff and dsniff:
    #         offset = niso.time_zero_offset
    #         nxs = nsniff.xs - offset
    #         ys = (nsniff.ys - nbs) / (dsniff.ys - dbs)
    #
    #         g.new_series(nxs, ys,
    #                      plotid=i,
    #                      type='scatter',
    #                      fit=False)
    #     xs = niso.offset_xs
    #     ys = (niso.ys - nbs) / (diso.ys - dbs)
    #     g.new_series(xs, ys,
    #                  fit=(fit.fit, fit.error_type),
    #                  filter_outliers_dict=fd,
    #                  truncate=trunc,
    #                  add_tools=add_tools,
    #                  plotid=i)
    #     return xs

    def _get_sniff_visible(self, fit, i):
        v = self.component.get_eq_visible(i)
        return fit.use_sniff or v

    # def _plot_signal(self, add_tools, fd, fit, trunc, g, i, isok, unk):
    #     xs = []
    #     if "/" in isok:
    #         return self._plot_ratio(add_tools, fd, fit, g, i, isok, trunc, unk)
    #     else:
    #         eq_only = self.component.get_eq_only_visible(0)
    #         if not eq_only:
    #             display_sniff = self._get_sniff_visible(fit, 0)
    #         else:
    #             display_sniff = True
    #
    #         # print i, ' eq_only: ', eq_only, 'display sniff: ', display_sniff
    #         if isok not in unk.isotopes:
    #             return []
    #         iso = unk.isotopes[isok]
    #
    #         iso.time_zero_offset = self.tool.time_zero_offset
    #
    #         if display_sniff:
    #             # xs = [1,2,3,4]
    #             # g.new_series(xs, [1,2,3,4],
    #             #              plotid=i,
    #             #              type='scatter',
    #             #              fit=False)
    #
    #             sniff = iso.sniff
    #             if sniff:
    #                 xs = sniff.offset_xs
    #                 g.new_series(xs, sniff.ys,
    #                              plotid=i,
    #                              type='scatter',
    #                              fit=False)
    #
    #         if not eq_only:
    #             iso.trait_setq(fit=fit.fit, error_type=fit.error_type)
    #             iso.filter_outlier_dict = fd
    #
    #             xs, ys = iso.offset_xs, iso.ys
    #             g.new_series(xs, ys,
    #                          fit=(fit.fit, fit.error_type),
    #                          filter_outliers_dict=fd,
    #                          truncate=trunc,
    #                          add_tools=add_tools,
    #                          plotid=i)
    #
    #             # iso.set_fit(fit, notify=False)
    #             iso.dirty = True
    #         return xs

    def _set_name(self):
        if not self.name:
            super(IsotopeEvolutionEditor, self)._set_name()

    # def _rebuild_graph(self):
    # fits = list(self._graph_generator())
    #     if not fits:
    #         return
    #
    #     self.graphs = []
    #     unk = self.analyses
    #     n = len(unk)
    #     r, c = 1, 1
    #     if n >= 2:
    #         while n > r * c:
    #             c += 1
    #             if c >= 7:
    #                 r += 1
    #
    #     cg = self._container_factory((r, c))
    #     if self.component:
    #         self.component.on_trait_change(self.rebuild_graph, 'replot_needed', remove=True)
    #         cg.set_dicts(self.component.get_dicts())
    #
    #     self.component = cg
    #     cg.on_trait_change(self._rebuild_graph, 'replot_needed')
    #
    #     add_tools = n == 1
    #     for j, unk in enumerate(self.analyses):
    #         set_ytitle = j % c == 0
    #         padding = [40, 10, 40, 40]
    #
    #         set_xtitle = True if r == 1 else j >= (n / r)
    #
    #         g = self._graph_factory(add_context_menu=False)
    #
    #         plot_kw = dict(padding=padding,
    #                        title=unk.record_id)
    #         with g.no_regression(refresh=False):
    #             ma = -Inf
    #             set_x_flag = False
    #             i = 0
    #
    #             for fit in fits:
    #                 set_x_flag = True
    #                 isok = fit.name
    #                 if set_ytitle:
    #                     plot_kw['ytitle'] = '{} (fA)'.format(isok)
    #
    #                 if set_xtitle:
    #                     plot_kw['xtitle'] = 'Time (s)'
    #
    #                 g.new_plot(**plot_kw)
    #                 fd = dict(iterations=fit.filter_iterations,
    #                           std_devs=fit.filter_std_devs,
    #                           filter_outliers=fit.filter_outliers)
    #                 trunc = fit.truncate
    #                 if isok.endswith('bs'):
    #                     xs = self._plot_baselines(add_tools, fd, fit, trunc, g, i, isok, unk)
    #                 else:
    #                     xs = self._plot_signal(add_tools, fd, fit, trunc, g, i, isok, unk)
    #
    #                 if len(xs):
    #                     ma = max(max(xs), ma)
    #                 else:
    #                     if not self.confirmation_dialog(
    #                             'No data for {} {}\n Do you want to continue?'.format(unk.record_id, fit.name)):
    #                         break
    #                 i += 1
    #
    #             unk.calculate_age(force=True)
    #             unk.sync_view()
    #
    #         if set_x_flag and ma > -Inf:
    #
    #             g.set_x_limits(0, ma * 1.1)
    #             g.refresh()
    #
    #         self.component.plotcontainer.add(g.plotcontainer)
    #         self.component.plotcontainer.on_trait_change(lambda x: g.plotcontainer.trait_set(bounds=x), 'bounds')
    #
    #         # need to store g in self.graphs to ensure bounds are updated
    #         self.graphs.append(g)

    # def traits_view(self):
    # v = View(UItem('component', style='custom', editor=InstanceEditor()))
    #     return v
    #
    # def _container_factory(self, shape):
    #     g = IsoEvoGraph(container_dict=dict(kind='g', shape=shape, spacing=(1, 1)))
    #     return g
    #
    # def _component_default(self):
    #     g = self._container_factory((1, 1))
    #
    #     return g
    #
    # def _tool_default(self):
    #     t = IsoEvoFitSelector(auto_update=False)
    #     return t

    # ============= deprecated =============================================
    def calculate_optimal_eqtime(self):
        # get x,y data
        self.info("========================================")
        self.info("           Optimal Eq. Results")
        self.info("========================================")

        from pychron.processing.utils.equilibration_utils import calc_optimal_eqtime

        for unk in self.analyses:
            for fit in self.tool.fits:
                if fit.fit and fit.use:
                    isok = fit.name
                    iso = unk.isotopes[isok]
                    sniff = iso.sniff
                    if sniff:
                        xs, ys = sniff.xs, sniff.ys
                        _rise_rates, ti, _vi = calc_optimal_eqtime(xs, ys)

                        xs, ys = iso.xs, iso.ys
                        m, b = polyfit(xs[:50], ys[:50], 1)
                        self.info(
                            "{:<12s} {}  t={:0.1f}  initial static pump={:0.2e} (fA/s)".format(
                                unk.record_id, isok, ti, m
                            )
                        )
                        g = self.graphs[unk.record_id]
                        if ti:
                            for plot in g.plots:
                                g.add_vertical_rule(ti, plot=plot)

        self.info("========================================")
        self.component.invalidate_and_redraw()

        # ============= EOF =============================================
        #         def simple_rebuild_graph(self):

    # # self._new_container = False
    #         self.rebuild_graph()
    #         # self._new_container = True

    #     def save(self):
    #         self._save(None, None, None)
    #
    #     def save_fits(self, fits, filters, progress=None):
    #         self._save(fits, filters, progress)
    #
    #     # private
    #     def _save(self, fits, filters, progress):
    #         proc = self.processor
    #
    #         ans = self.analyses
    #         n = len(ans)
    #         if progress is None:
    #             progress = proc.open_progress(n=n)
    #         else:
    #             progress.increase_max(n)
    #
    #         db = proc.db
    #         with db.session_ctx():
    #             ms = db.get_analyses_uuid([unk.uuid for unk in ans], analysis_only=True)
    #             args = [mi.id for mi in ms]
    #
    #             sid = self.processor.unique_id(args, time.time())
    #             fit_summary = ','.join(['{}{}'.format(si.name, si.fit)
    #                                     for si in self.tool.fits if si.use])
    #
    #             dbaction = db.add_proc_action('Set Fits for {} to {}. Fits={}'.format(ans[0].record_id,
    #                                                                                   ans[-1].record_id,
    #                                                                                   fit_summary),
    #                                           session=sid)
    #
    #             for unk, meas_analysis in zip(ans, ms):
    #                 progress.change_message('Saving Fits {}'.format(unk.record_id))
    #                 if fits and filters:
    #                     self._save_fit_dict(unk, meas_analysis, fits, filters, dbaction)
    #                 else:
    #                     self._save_fit(unk, meas_analysis, dbaction)
    #
    #                 proc.remove_from_cache(unk)
    #
    #         progress.soft_close()
    # def _save_fit_dict(self, unk, meas_analysis, fits, filters, dbaction):
    #         fit_hist = None
    #         include_baseline_error = True
    #         for fit_d, filter_d in zip(fits, filters):
    #             fname = name = fit_d['name']
    #             fit = fit_d['fit']
    #
    #             get_iso = lambda: unk.isotopes[name]
    #             if name.endswith('bs'):
    #                 fname = name[:-2]
    #                 get_iso = lambda: unk.isotopes[fname].baseline
    #
    #             if fname in unk.isotopes:
    #                 iso = get_iso()
    #                 if 'if n' in fit:
    #                     fit = eval(fit, {'n': iso.n})
    #                 elif 'if x' in fit:
    #                     if len(iso.xs):
    #                         fit = eval(fit, {'x': iso.xs[-1]})
    #                     else:
    #                         fit = 'linear'
    #
    #                 elif 'if d' in fit:
    #                     if len(iso.xs):
    #                         fit = eval(fit, {'d': iso.xs[-1] - iso.xs[0]})
    #                     else:
    #                         fit = 'linear'
    #
    #                 fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
    #                                              name, fit, 'SEM', filter_d, include_baseline_error)
    #                 fit_hist.action = dbaction
    #             else:
    #                 self.warning('no isotope {} for analysis {}'.format(fname, unk.record_id))

    # def _save_fit(self, unk, meas_analysis, dbaction):
    #
    #     tool_fits = [fi for fi in self.tool.fits
    #                  if fi.save and '/' not in fi.name]
    #
    #     time_zero_offset = self.tool.time_zero_offset or 0
    #     if not tool_fits:
    #         return
    #
    #     def in_tool_fits(f):
    #         name = f.isotope.molecular_weight.name
    #         if f.isotope.kind == 'baseline':
    #             name = '{}bs'.format(name)
    #         return next((t for t in tool_fits if t.name == name), None)
    #
    #     sel_hist = meas_analysis.selected_histories
    #     sel_fithist = sel_hist.selected_fits
    #     dbfits = None
    #     if sel_fithist:
    #         dbfits = sel_fithist.fits
    #
    #     fit_hist = None
    #     if dbfits:
    #         for dbfi in dbfits:
    #             tf = in_tool_fits(dbfi)
    #             if tf:
    #                 # use tool fit
    #                 fd = dict(filter_outliers=tf.filter_outliers,
    #                           iterations=tf.filter_iterations,
    #                           std_devs=tf.filter_std_devs)
    #
    #                 tool_fits.remove(tf)
    #                 fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
    #                                              tf.name, tf.fit, tf.error_type, fd,
    #                                              tf.include_baseline_error,
    #                                              time_zero_offset)
    #                 if not fit_hist:
    #                     db = self.processor.db
    #                     sess = db.get_session()
    #                     sess.rollback()
    #                     break
    #                 else:
    #                     fit_hist.action = dbaction
    #
    #             else:
    #                 fd = dict(filter_outliers=dbfi.filter_outliers,
    #                           iterations=dbfi.filter_outlier_iterations,
    #                           std_devs=dbfi.filter_outlier_std_devs)
    #
    #                 name = dbfi.isotope.molecular_weight.name
    #                 if dbfi.isotope.kind == 'baseline':
    #                     name = '{}bs'.format(name)
    #
    #                 fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
    #                                              name,
    #                                              dbfi.fit, dbfi.error_type, fd,
    #                                              dbfi.include_baseline_error,
    #                                              dbfi.time_zero_offset)
    #
    #     for fi in tool_fits:
    #         fd = dict(filter_outliers=fi.filter_outliers,
    #                   iterations=fi.filter_iterations,
    #                   std_devs=fi.filter_std_devs)
    #
    #         fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
    #                                      fi.name, fi.fit, fi.error_type, fd,
    #                                      fi.include_baseline_error)
    #         if not fit_hist:
    #             db = self.processor.db
    #             sess = db.get_session()
    #             sess.rollback()
    #             break
    #         else:
    #             fit_hist.action = dbaction
    #
    # def _save_db_fit(self, unk, meas_analysis, fit_hist, name, fit, et, filter_dict,
    #                  include_baseline_error, time_zero_offset):
    #     db = self.processor.db
    #     if name.endswith('bs'):
    #         name = name[:-2]
    #         # dbfit = unk.get_db_fit(meas_analysis, name, 'baseline')
    #         kind = 'baseline'
    #         iso = unk.isotopes[name].baseline
    #     else:
    #         # dbfit = unk.get_db_fit(meas_analysis, name, 'signal')
    #         kind = 'signal'
    #         iso = unk.isotopes[name]
    #
    #     f, e = convert_fit(fit)
    #     iso.fit = f
    #     iso.error_type = et or e
    #     iso.include_baseline_error = bool(include_baseline_error)
    #     iso.time_zero_offset = time_zero_offset
    #     if filter_dict:
    #         iso.set_filtering(filter_dict)
    #
    #     if fit_hist is None:
    #         fit_hist = db.add_fit_history(meas_analysis, user=db.save_username)
    #
    #     dbiso = next((i for i in meas_analysis.isotopes
    #                   if i.molecular_weight.name == name and
    #                   i.kind == kind), None)
    #
    #     if fit_hist is None:
    #         self.warning('Failed added fit history for {}'.format(unk.record_id))
    #         return
    #
    #     fod = iso.filter_outliers_dict
    #     db.add_fit(fit_hist, dbiso, fit=fit,
    #                error_type=iso.error_type,
    #                filter_outliers=fod['filter_outliers'],
    #                filter_outlier_iterations=fod['iterations'],
    #                filter_outlier_std_devs=fod['std_devs'],
    #                include_baseline_error=include_baseline_error,
    #                time_zero_offset=time_zero_offset)
    #
    #     # update isotoperesults
    #     v, e = float(iso.value), float(iso.error)
    #     db.add_isotope_result(dbiso, fit_hist,
    #                           signal_=v, signal_err=e)
    #     return fit_hist


#
# fitted=[]
# for fi in self.tool.fits:
#     if not fi.save:
#         continue
#
#     fd = dict(filter_outliers=fi.filter_outliers,
#               iterations=fi.filter_iterations,
#               std_devs=fi.filter_std_devs)
#
#     fit_hist, isoname, kind, added= self._save_db_fit(unk, meas_analysis, fit_hist,
#                                  fi.name, fi.fit, fi.error_type, fd)
#     if added:
#         fitted.append((isoname, kind))
#
# added=False
# for dbfi in dbfits:
#     if not next(((f,k) for f,k in fitted
#                  if dbfi.isotope.molecular_weight.name==f and dbfi.isotope.kind==k), None):
#         fd = dict(filter_outliers=dbfi.filter_outliers,
#                   iterations=dbfi.filter_iterations,
#                   std_devs=dbfi.filter_std_devs)
#
#         fit_hist=self._save_db_fit(unk, meas_analysis, fit_hist,
#                           dbfi.isotope.name , dbfi.fit, dbfi.error_type, fd)
#         print 'adding old fit for'.format(dbfi.isotope.name)
#         added=True
#
# if not added:
#     sess = self.processor.db.get_session()
#     sess.delete(fit_hist)
