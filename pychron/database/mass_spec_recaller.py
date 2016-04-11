## ===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
## ===============================================================================
#
#
#
# #from traits.etsconfig.api import ETSConfig
# #ETSConfig.toolkit = "qt4"
#
#
# from traits.api import HasTraits, List, Button, Instance, Enum
# from traitsui.api import View, Item, VGroup, HGroup, TabularEditor, TableEditor, ListStrEditor
#
# import numpy as np
# import math
#
#
# from pychron.graph.stacked_graph import StackedGraph
# from chaco.array_data_source import ArrayDataSource
# from pychron.graph.error_bar_overlay import ErrorBarOverlay
# from traitsui.table_column import ObjectColumn
# from traitsui.list_str_adapter import ListStrAdapter
# from pychron.database.selectors.massspec_selector import MassSpecSelector
# from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
#
#
# class LAdapter(ListStrAdapter):
# #    def get_bg_color(self, obj, trait, row):
#    def get_text_color(self, obj, trait, row):
# #        print obj, trait, row
#        o = getattr(obj, trait)[row]
#
#        if 'group_marker' in o:
#            return 'red'
#        else:
#            return 'black'
#    def get_text(self, obj, tr, ind):
#
#        o = getattr(obj, tr)[ind]
#        if 'group_marker' in o:
#            return '-----------------------'
#        else:
#            return o
#
# class MassSpecRecaller(HasTraits):
#    results = List
#    OK = Button
#    cancel = Button
#    append = Button
#    replace = Button
#
#    selector = Instance(MassSpecSelector)
#    selected_results = List
#
#
#    def _selector_default(self):
#        db = MassSpecDatabaseAdapter(name='massspecdata_local',
#                                  #host='129.138.12.131',
# #                                  user='massspec',
#                                  )
#        db.connect()
#        m = MassSpecSelector(_db=db,
#                             parameter='AnalysesTable.RID',
#                             criteria='21351',
#                             comparator='contains'
#                             )
#        m.title = ''
#        return m
#    def _append_fired(self):
#        self._load_selected_results()
#
#    def _replace_fired(self):
#        self.selected_results = []
#        self._load_selected_results()
#
#    def _OK_fired(self):
# #        self._open_ideogram()
# #        self._open_spectrum()
#        self.selected_results.append('group_marker1')
#
#    def _open_ideogram(self):
#        ages, errs = zip(*[(r._db_result.araranalyses[-1].Age,
#                             r._db_result.araranalyses[-1].ErrAge)
#                            for r in self.selected_results])
#
#        #errs from mass spec are 2sigma
#        errs = np.array(errs)
#        errs /= 2.0
#        g = self.build_ideogram(ages, errs)
#
#        for r in self.selected_results:
#            dbr = r._db_result
#            arar = dbr.araranalyses[-1]
#            print dbr.RID, arar.Age, arar.ErrAge
#
#        g.edit_traits()
#
#    def _open_spectrum(self):
#        ages, errs, ar39s = zip(*[(r._db_result.araranalyses[-1].Age,
#                             r._db_result.araranalyses[-1].ErrAge,
#                            r._db_result.araranalyses[-1].Tot39
#                             )
#                            for r in self.selected_results])
#
#        g = self.build_spectrum(ages, errs, ar39s)
#        g.edit_traits()
#
#    def _weighted_mean(self, x, errs):
#        x = np.asarray(x)
#        errs = np.asarray(errs)
#
#        weights = np.asarray(map(lambda e: 1 / e ** 2, errs))
#
#        wtot = weights.sum()
#        wmean = (weights * x).sum() / wtot
#        werr = wtot ** -0.5
#
#        return wmean, werr
#
#    def _calc_mswd(self, x, errs):
#        x = np.asarray(x)
#        errs = np.asarray(errs)
#
#        xmean_u = x.mean()
#        xmean_w, _err = self._weighted_mean(x, errs)
#
#        ssw = (x - xmean_w) ** 2 / errs ** 2
#        ssu = (x - xmean_u) ** 2 / errs ** 2
#
#        d = 1.0 / (len(x) - 1)
#        mswd_w = d * ssw.sum()
#        mswd_u = d * ssu.sum()
#
#        return  mswd_u, mswd_w
#
#    def build_spectrum(self, ages, errors, ar39s):
#        g = StackedGraph(panel_height=200,
#                         equi_stack=False
#                         )
#
#        g.new_plot()
#
#        xs = []
#        ys = []
#        es = []
#        sar = sum(ar39s)
#        prev = 0
#
#        for ai, ei, ar in zip(ages, errors, ar39s):
# #            print ai, ei
#            xs.append(prev)
#            ys.append(ai)
#            es.append(ei)
#
#            s = 100 * ar / sar
#
#            xs.append(s)
#            ys.append(ai)
#            es.append(ei)
#            prev = s
#
#        ys.append(ai)
#        es.append(ei)
#        xs.append(100)
#
#        #main age line
# #        g.new_series(xs, ys)
#        #error box
#        ox = xs[:]
#        xs.reverse()
#        xp = ox + xs
#
#        yu = [yi + ei for (yi, ei) in zip(ys, es)]
#
#        yl = [yi - ei for (yi, ei) in zip(ys, es)]
#        yl.reverse()
#
#        yp = yu + yl
#        g.new_series(x=xp, y=yp, type='polygon')
#        g.set_y_limits(min=min(ys) * 0.95, max=max(ys) * 1.05)
#        return g
#
#    def build_ideogram(self, ages, errors):
#
#        g = StackedGraph(panel_height=200,
#                         equi_stack=False
#                         )
#
#        g.new_plot()
#        g.add_minor_xticks()
#        g.add_minor_xticks(placement='opposite')
#        g.add_minor_yticks()
#        g.add_minor_yticks(placement='opposite')
#        g.add_opposite_ticks()
#
#        g.set_x_title('Age (Ma)')
#        g.set_y_title('Relative Probability')
#
#        mi = 26.60839
#        ma = 30.02082
#        g.set_x_limits(min=mi, max=ma)
#
#        n = 500
#        bins = np.linspace(mi, ma, n)
#        probs = np.zeros(n)
#
#        ages = np.asarray(ages)
#        wm, we = self._weighted_mean(ages, errors)
#        print ages
# print 'exception', errors
#        print 'waieht', wm, we
#        for ai, ei in zip(ages, errors):
#            for j, bj in enumerate(bins):
#                #calculate the gaussian prob
#                #p=1/(2*p*sigma2) *exp (-(x-u)**2)/(2*sigma2)
#                #see http://en.wikipedia.org/wiki/Normal_distribution
#                delta = math.pow(ai - bj, 2)
#                prob = math.exp(-delta / (2 * ei * ei)) / (math.sqrt(2 * math.pi * ei * ei))
#
#                #cumulate probablities
#                probs[j] += prob
#
#        minp = min(probs)
#        maxp = max(probs)
#        g.set_y_limits(min=minp, max=maxp * 1.05)
#
#        g.new_series(x=bins, y=probs)
#
#        dp = maxp - minp
#
#        s, _p = g.new_series([wm], [maxp - 0.85 * dp], type='scatter', color='black')
#        s.underlays.append(ErrorBarOverlay(component=s))
#        nsigma = 2
#        s.xerror = ArrayDataSource([nsigma * we])
#
#        g.new_plot(bounds=[50, 100])
#        g.add_minor_xticks(plotid=1, placement='opposite')
#
#        g.add_minor_yticks(plotid=1)
#        g.add_minor_yticks(plotid=1, placement='opposite')
#
#        g.add_opposite_ticks(plotid=1)
#
#        g.set_y_title('Analysis #', plotid=1)
#        g.set_axis_traits(orientation='right', plotid=1, axis='y')
#
#        n = zip(ages, errors)
# #        ages.sort()
#        n = sorted(n, key=lambda x:x[0])
#        ages, errors = zip(*n)
# #        print ages, errors
#        for ni in n:
#            print ni
#        s, _p = g.new_series(ages, range(1, len(ages) + 1, 1), type='scatter', marker='circle', plotid=1)
#        s.underlays.append(ErrorBarOverlay(component=s))
#        s.xerror = ArrayDataSource(errors)
#
#        g.set_y_limits(min=0, max=len(ages) + 1, plotid=1)
#
#        return g
#
#    def _load_selected_results(self):
#        for r in self.selector.selected:
#            if r not in self.selected_results:
#                self.selected_results.append(r.rid)
#
#    def traits_view(self):
#        ad = self.selector.tabular_adapter()
#        editor = TabularEditor(adapter=ad,
#                                        drag_move=True,
#                                        operations=['delete', 'move'])
#
#        cols = [
#                ObjectColumn(name='rid', editable=False, width=175),
#                ObjectColumn(name='ridt', editable=False, width=175),
#                ]
#
#        editor = TableEditor(columns=cols,
#                             reorderable=True,
#                             sortable=True,
#                             show_toolbar=True)
#
#        editor = ListStrEditor(multi_select=True,
#                               editable=False,
#                               adapter=LAdapter(can_edit=False)
#                               )
#        v = View(
#                  HGroup(
#                         Item('selector', style='custom', show_label=False),
#                          VGroup(Item('append', show_label=False),
#                                 Item('replace', show_label=False)),
#                          VGroup(
#                                 Item('selected_results', show_label=False, style='custom',
#
#                                      editor=editor
#                                      ),
#                                 Item('OK'),
#                                 Item('cancel')
#                                 )
#                         ),
#                 id='recaller',
#                  height=600,
#                  resizable=True,
#                  )
#        return v
#
# if __name__ == '__main__':
#
#
#
#    from pychron.core.helpers.logger_setup import logging_setup
#    logging_setup('massspecrecaller')
#    m = MassSpecRecaller()
#    m.selector._search_()
#    m.configure_traits()
##======== EOF ================================
