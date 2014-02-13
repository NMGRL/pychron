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
#from chaco.label import Label
from traits.api import Instance, Bool, Any
from traitsui.api import View, UItem, InstanceEditor
#============= standard library imports ========================
from numpy import Inf, polyfit

#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.core.helpers.fits import convert_fit
from pychron.processing.fits.iso_evo_fit_selector import IsoEvoFitSelector
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
#from pychron.core.ui.thread import Thread

def fits_equal(dbfit, fit, fod):
    """
        return True if fits are the same
    """
    same = False
    if dbfit.fit == fit:
        a = fod['filter_outliers'] == dbfit.filter_outliers
        b = fod['iterations'] == dbfit.filter_outlier_iterations
        c = fod['std_devs'] == dbfit.filter_outlier_std_devs
        return a and b and c

    return same


class IsotopeEvolutionEditor(GraphEditor):
    component = Any
    #component = Instance(Container)
    #component = Instance(VPlotContainer)
    #component = Instance(HPlotContainer)
    #component = Instance(GridPlotContainer)
    # graphs = Dict
    _suppress_update = Bool

    #tool = Instance(IsoEvoFitSelector, ())
    tool = Instance(IsoEvoFitSelector)
    pickle_path = 'iso_fits'
    unpack_peaktime = True
    update_on_analyses = False
    calculate_age = True

    def _set_name(self):
        if not self.name:
            super(IsotopeEvolutionEditor, self)._set_name()

    def _tool_default(self):
        t = IsoEvoFitSelector(auto_update=False)
        return t

    def save(self):
        self._save(None, None, None)

    def _save(self, fits, filters, progress):
        proc = self.processor
        n = len(self.analyses)
        if progress is None:
            progress = proc.open_progress(n=n)
        else:
            progress.increase_max(n)

        db = proc.db
        for unk in self.analyses:
            progress.change_message('Saving Fits {}'.format(unk.record_id))

            meas_analysis = db.get_analysis_uuid(unk.uuid)
            if fits and filters:
                self._save_fit_dict(unk, meas_analysis, fits, filters)
            else:
                self._save_fit(unk, meas_analysis)

                #prog.change_message('{} Saving ArAr age'.format(unk.record_id))
                #proc.save_arar(unk, meas_analysis)
        progress.soft_close()

    def save_fits(self, fits, filters, progress=None):
        self._save(fits, filters, progress)

    def _save_fit_dict(self, unk, meas_analysis, fits, filters):
        fit_hist = None
        for fit_d, filter_d in zip(fits, filters):
            fname = name = fit_d['name']
            fit = fit_d['fit']

            get_iso = lambda: unk.isotopes[name]
            if name.endswith('bs'):
                fname = name[:-2]
                get_iso = lambda: unk.isotopes[fname].baseline

            if fname in unk.isotopes:
                iso = get_iso()
                if 'if n' in fit:
                    fit = eval(fit, {'n': iso.n})
                elif 'if x' in fit:
                    if len(iso.xs):
                        fit = eval(fit, {'x': iso.xs[-1]})
                    else:
                        fit = 'linear'

                elif 'if d' in fit:
                    if len(iso.xs):
                        fit = eval(fit, {'d': iso.xs[-1] - iso.xs[0]})
                    else:
                        fit = 'linear'

                fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                             name, fit, filter_d)
            else:
                self.warning('no isotope {} for analysis {}'.format(fname, unk.record_id))

    def _save_fit(self, unk, meas_analysis):

        tool_fits = [fi for fi in self.tool.fits if fi.save]
        if not tool_fits:
            return

        # fit_hist = None

        def in_tool_fits(f):
            name = f.isotope.molecular_weight.name
            if f.isotope.kind == 'baseline':
                name = '{}bs'.format(name)
            return next((t for t in tool_fits if t.name == name), None)

        sel_hist = meas_analysis.selected_histories
        sel_fithist = sel_hist.selected_fits
        dbfits = sel_fithist.fits
        print dbfits
        fit_hist = None
        if dbfits:
            for dbfi in dbfits:
                tf = in_tool_fits(dbfi)
                if tf:
                    #use tool fit
                    fd = dict(filter_outliers=fi.filter_outliers,
                              iterations=fi.filter_iterations,
                              std_devs=fi.filter_std_devs)

                    tool_fits.remove(tf)
                    fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                                 tf.name, tf.fit, tf.error_type, fd)
                    if not fit_hist:
                        db = self.processor.db
                        sess = db.get_session()
                        sess.rollback()
                        break
                else:
                    fd = dict(filter_outliers=dbfi.filter_outliers,
                              iterations=dbfi.filter_outlier_iterations,
                              std_devs=dbfi.filter_outlier_std_devs)

                    name = dbfi.isotope.molecular_weight.name
                    if dbfi.isotope.kind == 'baseline':
                        name = '{}bs'.format(name)

                    fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                                 name,
                                                 dbfi.fit, dbfi.error_type, fd)

        for fi in tool_fits:
            fd = dict(filter_outliers=fi.filter_outliers,
                      iterations=fi.filter_iterations,
                      std_devs=fi.filter_std_devs)

            fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                         fi.name, fi.fit, fi.error_type, fd)
            if not fit_hist:
                db = self.processor.db
                sess = db.get_session()
                sess.rollback()
                break

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

    def _save_db_fit(self, unk, meas_analysis, fit_hist, name, fit, et, filter_dict):
        db = self.processor.db
        print 'save fit', name
        if name.endswith('bs'):
            name = name[:-2]
            # dbfit = unk.get_db_fit(meas_analysis, name, 'baseline')
            kind = 'baseline'
            iso = unk.isotopes[name].baseline
        else:
            # dbfit = unk.get_db_fit(meas_analysis, name, 'signal')
            kind = 'signal'
            iso = unk.isotopes[name]

        if filter_dict:
            iso.filter_outliers_dict = filter_dict.copy()

        v = iso.uvalue
        f, e = convert_fit(fit)
        iso.fit = f
        iso.error_type = et or e

        if fit_hist is None:
            fit_hist = db.add_fit_history(meas_analysis, user=db.save_username)

        dbiso = next((iso for iso in meas_analysis.isotopes
                      if iso.molecular_weight.name == name and
                         iso.kind == kind), None)

        if fit_hist is None:
            self.warning('Failed added fit history for {}'.format(unk.record_id))
            return

        fod = iso.filter_outliers_dict
        db.add_fit(fit_hist, dbiso, fit=fit,
                   error_type=iso.error_type,
                   filter_outliers=fod['filter_outliers'],
                   filter_outlier_iterations=fod['iterations'],
                   filter_outlier_std_devs=fod['std_devs'])
        #update isotoperesults
        v, e = float(v.nominal_value), float(v.std_dev)
        db.add_isotope_result(dbiso, fit_hist,
                              signal_=v, signal_err=e)
        return fit_hist

    def _plot_baselines(self, add_tools, fd, fit, trunc, g, i, isok, unk):
        isok = isok[:-2]
        iso = unk.isotopes[isok]
        xs, ys = iso.baseline.xs, iso.baseline.ys
        g.new_series(xs, ys,
                     fit=fit.fit,
                     filter_outliers_dict=fd,
                     add_tools=add_tools,
                     plotid=i)
        return xs

    def _plot_signal(self, add_tools, fd, fit, trunc, g, i, isok, unk):
        if not isok in unk.isotopes:
            return []

        display_sniff = True
        iso = unk.isotopes[isok]
        if display_sniff:
            sniff = iso.sniff
            if sniff:
                g.new_series(sniff.xs, sniff.ys,
                             plotid=i,
                             type='scatter',
                             fit=False)
        xs, ys = iso.xs, iso.ys
        g.new_series(xs, ys,
                     fit=(fit.fit, fit.error_type),
                     filter_outliers_dict=fd,
                     truncate=trunc,
                     add_tools=add_tools,
                     plotid=i)
        return xs

    def _rebuild_graph(self):
        self.__rebuild_graph()
        # n = len(self.unknowns)
        # prog = None
        # if n > 1:
        #     prog = self.processor.open_progress(n)
        #     prog.change_message('Loading Plots')
        #
        # t = Thread(target=self.__rebuild_graph)
        # t.start()
        # t.join()
        #
        # if prog:
        #     prog.close()

    def __rebuild_graph(self):
        fits = list(self._graph_generator())
        if not fits:
            return

        self.graphs = []
        unk = self.analyses
        n = len(unk)
        r, c = 1, 1
        if n >= 2:
            while n > r * c:
                c += 1
                if c >= 7:
                    r += 1

        cg = self._container_factory((r, c))
        self.component = cg

        add_tools = not self.tool.auto_update or n == 1

        for j, unk in enumerate(self.analyses):
            set_ytitle = j % c == 0
            padding = [40, 10, 40, 40]

            set_xtitle = True if r == 1 else j >= (n / r)

            g = self._graph_factory(add_context_menu=False)

            plot_kw = dict(padding=padding,
                           title=unk.record_id)

            with g.no_regression(refresh=False):
                ma = -Inf
                set_x_flag = False
                i = 0
                for fit in fits:
                    set_x_flag = True
                    isok = fit.name
                    if set_ytitle:
                        plot_kw['ytitle'] = '{} (fA)'.format(isok)

                    if set_xtitle:
                        plot_kw['xtitle'] = 'Time (s)'

                    g.new_plot(**plot_kw)
                    fd = dict(iterations=fit.filter_iterations,
                              std_devs=fit.filter_std_devs,
                              filter_outliers=fit.filter_outliers)
                    trunc = fit.truncate

                    if isok.endswith('bs'):
                        xs = self._plot_baselines(add_tools, fd, fit, trunc, g, i, isok, unk)
                    else:
                        xs = self._plot_signal(add_tools, fd, fit, trunc, g, i, isok, unk)

                    if len(xs):
                        ma = max(max(xs), ma)
                    else:
                        if not self.confirmation_dialog(
                                'No data for {} {}\n Do you want to continue?'.format(unk.record_id, fit.name)):
                            break
                    i += 1

            if set_x_flag and ma > -Inf:
                g.set_x_limits(0, ma * 1.1)
                g.refresh()

            self.component.plotcontainer.add(g.plotcontainer)
            self.component.plotcontainer.on_trait_change(lambda x: g.plotcontainer.trait_set(bounds=x), 'bounds')

            #need to store g in self.graphs to ensure bounds are updated
            self.graphs.append(g)

    def traits_view(self):
        v = View(UItem('component', style='custom', editor=InstanceEditor()))
        return v

    def _component_default(self):
        g = self._container_factory((1, 1))
        return g

    def _container_factory(self, shape):
        g = Graph(container_dict=dict(kind='g', shape=shape, spacing=(1, 1)))
        return g

    #============= deprecated =============================================
    def calculate_optimal_eqtime(self):
        # get x,y data
        self.info('========================================')
        self.info('           Optimal Eq. Results')
        self.info('========================================')

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
                            '{:<12s} {}  t={:0.1f}  initial static pump={:0.2e} (fA/s)'.format(unk.record_id, isok, ti,
                                                                                               m))
                        g = self.graphs[unk.record_id]
                        if ti:
                            for plot in g.plots:
                                g.add_vertical_rule(ti, plot=plot)

        self.info('========================================')
        self.component.invalidate_and_redraw()

        #============= EOF =============================================
