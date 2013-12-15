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
from threading import Thread
#from chaco.label import Label
from traits.api import Instance, Dict, Bool, Any, on_trait_change
from traitsui.api import View, UItem, InstanceEditor
#============= standard library imports ========================
from numpy import Inf, polyfit

#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.helpers.fits import convert_fit
from pychron.processing.fits.iso_evo_fit_selector import IsoEvoFitSelector
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
#from pychron.ui.thread import Thread


class IsotopeEvolutionEditor(GraphEditor):
    component = Any
    #component = Instance(Container)
    #component = Instance(VPlotContainer)
    #component = Instance(HPlotContainer)
    #component = Instance(GridPlotContainer)
    graphs = Dict
    _suppress_update = Bool

    #tool = Instance(IsoEvoFitSelector, ())
    tool = Instance(IsoEvoFitSelector)
    pickle_path = 'iso_fits'
    unpack_peaktime = True
    update_on_unknowns = False
    calculate_age = True

    @on_trait_change('tool:save_event')
    def _handle_save_event(self):
        self.save_event=True

    def _set_name(self):
        if not self.name:
            super(IsotopeEvolutionEditor, self)._set_name()

    def _tool_default(self):
        t = IsoEvoFitSelector(auto_update=False)
        return t

    def save(self):
        proc = self.processor
        prog = proc.open_progress(n=len(self.unknowns))

        db = proc.db
        for unk in self.unknowns:
            prog.change_message('{} Saving fits'.format(unk.record_id))

            meas_analysis = db.get_analysis_uuid(unk.uuid)
            self._save_fit(unk, meas_analysis)

            #prog.change_message('{} Saving ArAr age'.format(unk.record_id))
            #proc.save_arar(unk, meas_analysis)
        prog.close()

    def save_fits(self, fits, filters):
        proc = self.processor
        prog = proc.open_progress(n=len(self.unknowns))

        db = proc.db
        for unk in self.unknowns:
            prog.change_message('{} Saving fits'.format(unk.record_id))

            meas_analysis = db.get_analysis_uuid(unk.uuid)
            self._save_fit_dict(unk, meas_analysis, fits, filters)

            #if unk.analysis_type in ('cocktail', 'unknown'):
            #msg = '{} Saving ArAr age'.format(unk.record_id)
            #prog.change_message(msg)

            #update arar table
            #proc.save_arar(unk, meas_analysis)

            #else:
            #    prog.increment()


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
                    fit = eval(fit, {'x': iso.xs[-1]})
                elif 'if d' in fit:
                    fit = eval(fit, {'d': iso.xs[-1] - iso.xs[0]})

                fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                             name, fit, filter_d)
            else:
                self.warning('no isotope {} for analysis {}'.format(fname, unk.record_id))


    def _save_fit(self, unk, meas_analysis):
        fit_hist = None

        for fi in self.tool.fits:
            if not fi.use:
                continue

            fd = dict(use=fi.use_filter,
                      n=fi.filter_iterations,
                      std_devs=fi.filter_std_devs)

            fit_hist = self._save_db_fit(unk, meas_analysis, fit_hist,
                                         fi.name, fi.fit, fd)

    def _save_db_fit(self, unk, meas_analysis, fit_hist, name, fit, filter_dict):
        db = self.processor.db
        # print name
        if name.endswith('bs'):
            name = name[:-2]
            dbfit = unk.get_db_fit(name, meas_analysis, 'baseline')
            kind = 'baseline'
            iso = unk.isotopes[name].baseline
        else:
            dbfit = unk.get_db_fit(name, meas_analysis, 'signal')
            kind = 'signal'
            iso = unk.isotopes[name]

        if filter_dict:
            iso.filter_outliers = filter_dict['use']
            iso.filter_outlier_iterations = filter_dict['n']
            iso.filter_outlier_std_devs = filter_dict['std_devs']

        if dbfit != fit:
            v = iso.uvalue
            iso.fit = convert_fit(fit)

            if fit_hist is None:
                fit_hist = db.add_fit_history(meas_analysis, user=db.save_username)

            dbiso = next((iso for iso in meas_analysis.isotopes
                          if iso.molecular_weight.name == name and
                             iso.kind == kind), None)

            #if kind=='baseline':
            #    for ix in meas_analysis.isotopes:
            #        print ix.kind, ix.molecular_weight.name, kind, name, dbiso
            if fit_hist is None:
                self.warning('Failed added fit history for {}'.format(unk.record_id))
                return

            db.add_fit(fit_hist, dbiso, fit=fit,
                       filter_outliers=iso.filter_outliers,
                       filter_outlier_iterations=iso.filter_outlier_iterations,
                       filter_outlier_std_devs=iso.filter_outlier_std_devs)
            #update isotoperesults
            v, e = float(v.nominal_value), float(v.std_dev)
            db.add_isotope_result(dbiso, fit_hist,
                                  signal_=v, signal_err=e)

            self.debug('adding {} fit {} - {}'.format(kind, name, fit))

        return fit_hist

    def _plot_baselines(self, add_tools, fd, fit, trunc, g, i, isok, unk):
        isok = isok[:-2]
        iso = unk.isotopes[isok]
        #iso.baseline.fit = fit.fit
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
                     fit=fit.fit,
                     filter_outliers_dict=fd,
                     truncate=trunc,
                     add_tools=add_tools,
                     plotid=i)
        return xs


    def _rebuild_graph(self):
        n = len(self.unknowns)
        prog = None
        if n > 1:
            prog = self.processor.open_progress(n)
            prog.change_message('Loading Plots')

        t = Thread(target=self.__rebuild_graph)
        t.start()
        t.join()

        if prog:
            prog.close()


    def __rebuild_graph(self):
        fits = list(self._graph_generator())
        if not fits:
            return

        unk = self.unknowns
        n = len(unk)
        r, c = 1, 1
        if n >= 2:
            while n > r * c:
                c += 1
                if c >= 7:
                    r += 1

        cg=self._container_factory((r, c))
        self.component = cg#.plotcontainer

        #prog = None
        n = len(self.unknowns)
        #if n > 1:
        #    prog = self.processor.open_progress(n)

        #add_tools = bind_index = not self.tool.auto_update or n == 1
        add_tools = not self.tool.auto_update or n == 1

        for j, unk in enumerate(self.unknowns):
            set_ytitle = j%c == 0
            padding=[40,10,40,40]

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

                    p=g.new_plot(**plot_kw)

                    fd = dict(iterations=fit.filter_iterations,
                              std_devs=fit.filter_std_devs,
                              filter_outliers=fit.use_filter)
                    trunc=fit.truncate

                    if isok.endswith('bs'):
                        xs = self._plot_baselines(add_tools, fd, fit, trunc, g, i, isok, unk)
                    else:
                        xs = self._plot_signal(add_tools, fd, fit, trunc, g, i, isok, unk)

                    ma = max(max(xs), ma)
                    i += 1

            if set_x_flag:
                g.set_x_limits(0, ma * 1.1)
                g.refresh()

            self.component.plotcontainer.add(g.plotcontainer)
            #print 'aaa',self.component.plotcontainer, g.plotcontainer

    def traits_view(self):
        v=View(UItem('component', style='custom', editor=InstanceEditor()))
        #v = View(UItem('component',
        #               style='custom',
        #               editor=ComponentEditor()))
        return v

    def _component_default(self):
        g=self._container_factory((1, 1))
        return g

    def _container_factory(self, shape):
        g=Graph(container_dict=dict(kind='g', shape=shape, spacing=(1,1)))
        return g
        #return GridPlotContainer(shape=shape,
        #                         spacing=(1, 1))

    #============= deprecated =============================================
    def calculate_optimal_eqtime(self):
        # get x,y data
        self.info('========================================')
        self.info('           Optimal Eq. Results')
        self.info('========================================')

        from pychron.processing.utils.equilibration_utils import calc_optimal_eqtime

        for unk in self.unknowns:

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
