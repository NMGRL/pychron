#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Property, List, on_trait_change, Bool, \
    Str, CInt, Int, Tuple, Color
from traitsui.api import View, UItem, VGroup, HGroup, spring
from pychron.graph.graph import Graph

from pychron.graph.regression_graph import StackedRegressionGraph
# from pychron.helpers.traitsui_shortcuts import instance_item
from pychron.processing.analyses.view.automated_run_view import AutomatedRunAnalysisView
from pychron.pychron_constants import PLUSMINUS
#from pychron.processing.analyses.analysis_view import AutomatedRunAnalysisView
from pychron.processing.arar_age import ArArAge
# from pychron.helpers.formatting import floatfmt
from pychron.ui.text_table import MultiTextTableAdapter
# from pychron.database.records.ui.analysis_summary import SignalAdapter
from pychron.loggable import Loggable
from pychron.ui.custom_label_editor import CustomLabel
from pychron.ui.gui import invoke_in_main_thread

#============= standard library imports ========================
#============= local library imports  ==========================

HEIGHT = 250
ERROR_WIDTH = 10
VALUE_WIDTH = 12

# class SignalAdapter(SimpleTextTableAdapter):
class SignalAdapter(MultiTextTableAdapter):
    columns = [
        [
            ('Iso.', 'isotope', str, 6),
            ('Det.', 'detector', str, 5),
            ('Fit', 'fit', str, 4),
            ('Intercept', 'intercept_value', None, VALUE_WIDTH),
            (u'{}1s'.format(PLUSMINUS), 'intercept_error', None, ERROR_WIDTH),
            (u'{}%'.format(PLUSMINUS), 'intercept_error_percent', str, ERROR_WIDTH - 1),
            ('Raw(fA)', 'raw_value', None, VALUE_WIDTH),
            (u'{}1s'.format(PLUSMINUS), 'raw_error', None, ERROR_WIDTH),
            (u'{}%'.format(PLUSMINUS), 'raw_error_percent', str, ERROR_WIDTH - 1),
        ],
        [
            ('Iso.', 'isotope', str, 6),
            ('Det.', 'detector', str, 5),
            ('Fit', 'baseline_fit', str, 4),
            ('Baseline', 'baseline_value', None, VALUE_WIDTH),
            (u'{}1s'.format(PLUSMINUS), 'baseline_error', None, ERROR_WIDTH),
            (u'{}%'.format(PLUSMINUS), 'baseline_error_percent', str, ERROR_WIDTH - 1),
            ('Blank', 'blank_value', None, VALUE_WIDTH),
            (u'{}1s'.format(PLUSMINUS), 'blank_error', None, ERROR_WIDTH),
            (u'{}%'.format(PLUSMINUS), 'blank_error_percent', str, ERROR_WIDTH - 1),
        ]
    ]


# class PlotPanelHandler(ViewableHandler):
#    pass
from traits.api import HasTraits, Any
from traitsui.api import ListEditor


class TraitsContainer(HasTraits):
    model = Any

    def trait_context(self):
        """ Use the model object for the Traits UI context, if appropriate.
        """
        if self.model:
            return {'object': self.model}
        return super(TraitsContainer, self).trait_context()

#class DisplayContainer(TraitsContainer):
#    model = Any
#    def _get_display_group(self):
#        results_grp = Group(
##                             HGroup(
##                                   Item('correct_for_baseline'),
##                                   Item('correct_for_blank'),
##                                   spring),
#                            UItem('display_signals',
#                                  editor=FastTextTableEditor(adapter=SignalAdapter(),
#                                                         bg_color='lightyellow',
#                                                         header_color='lightgray',
#                                                         font_size=10,
#                                                         ),
##                                          width=0.8
#                                         ),
#                                label='Results'
#                            )
#
#        ratios_grp = Group(UItem('display_ratios',
#                                         editor=FastTextTableEditor(adapter=RatiosAdapter(),
#                                                         bg_color='lightyellow',
#                                                         header_color='lightgray'
#                                                         ),
#                                        ),
#                           label='Ratios'
#                           )
#        summary_grp = Group(
#                           UItem('display_summary',
#                                 editor=FastTextTableEditor(adapter=ValueErrorAdapter(),
#                                                        bg_color='lightyellow',
#                                                        header_color='lightgray'
#                                                        )
#                                 ),
#                            label='Summary'
#                          )
#        display_grp = Group(
#                            results_grp,
#                            ratios_grp,
#                            summary_grp,
#                            layout='tabbed'
#                            )
#
#        return display_grp
#
#    def traits_view(self):
#        v = View(
#               VGroup(
#                      Item('ncounts'),
#                      self._get_display_group()
#                     ),
#               )
#        return v

class GraphContainer(TraitsContainer):

#    graphs = List
#    selected_tab = Any
#    label = Str
#     def _selected_tab_changed(self):
#         print 'sel', self.selected_tab


    def traits_view(self):
        v = View(
            VGroup(
                HGroup(spring,
                       CustomLabel('plot_title',
                                   weight='bold',
                                   size=14),
                       spring
                ),
                UItem(
                    'graphs',
                    editor=ListEditor(use_notebook=True,
                                      selected='selected_graph',
                                      page_name='.page_name'
                    ),
                    style='custom'
                )
            )
        )
        return v


class PlotPanel(Loggable):
    graph_container = Instance(GraphContainer)
    #display_container = Instance(DisplayContainer)

    analysis_view = Instance(AutomatedRunAnalysisView, ())

    arar_age = Instance(ArArAge)

    isotope_graph = Instance(Graph, ())
    peak_center_graph = Instance(Graph, ())
    selected_graph = Any

    graphs = Tuple

    plot_title = Str
    #analysis_id=DelegatesTo('analysis_view')

    ncounts = Property(Int(enter_set=True, auto_set=False), depends_on='_ncounts')
    _ncounts = CInt

    ncycles = Property(Int(enter_set=True, auto_set=False),
                       depends_on='_ncycles')
    _ncycles = CInt

    current_cycle = Str
    current_color = Color

    detectors = List
    #fits = List
    isotopes = Property(depends_on='detectors')

    stack_order = 'bottom_to_top'
    series_cnt = 0

    #ratio_display = Instance(DisplayController)
    #signal_display = Instance(DisplayController)
    #summary_display = Instance(DisplayController)
    #fit_display = Instance(DisplayController)
    #
    #display_signals = List
    #display_ratios = List
    #display_summary = List
    #    refresh = Event
    total_counts = CInt

    is_baseline = Bool(False)
    is_peak_hop = Bool(False)

    ratios = ['Ar40:Ar36', 'Ar40:Ar39', ]
    info_func = None

    refresh_age = True

    _plot_keys = List

    def set_peak_center_graph(self, graph):
        self.peak_center_graph = graph
        self.show_graph(graph)

    def show_graph(self, g):
        invoke_in_main_thread(self.trait_set, selected_graph=g)

    def show_isotope_graph(self):
        self.show_graph(self.isotope_graph)

    def info(self, *args, **kw):
        if self.info_func:
            self.info_func(*args, **kw)
        else:
            super(PlotPanel, self).info(*args, **kw)

    def reset(self):
        #self.clear_displays()

        self.isotope_graph.clear()
        self.peak_center_graph.clear()

    def create(self, dets):
        """
            dets: list of Detector instances
        """
        invoke_in_main_thread(self._create, dets)

    def _create(self, dets):
        self.reset()

        g = self.isotope_graph
        self.selected_graph = g

        self._plot_keys = []
        for det in dets:
            g.new_plot(
                ytitle='{} {} (fA)'.format(det.name, det.isotope),
                xtitle='time (s)',
                padding_left=70,
                padding_right=10)
            self._plot_keys.append(det.isotope)

        self.detectors = dets

        #def clear_displays(self):
        #    self._print_results()

        #def _make_display_summary(self):
        #    def factory(n, v):
        #        if isinstance(v, tuple):
        #            sv, se = v
        #        else:
        #            sv = v.nominal_value
        #            se = v.std_dev
        #
        #        return DisplayValue(name=n, value=sv, error=se)
        #
        #    arar_age = self.arar_age
        #    summary = []
        #    if arar_age:
        #        # call age first
        #        # loads all the other attrs
        #        age = arar_age.calculate_age()
        #        summary = [
        #                   factory(name, v) for name, v in
        #                   [
        #                    ('Age', age),
        #                    ('', ('', arar_age.age_error_wo_j)),
        #                    ('J', arar_age.j),
        #                    ('K/Ca', arar_age.kca),
        #                    ('K/Cl', arar_age.kcl),
        #                    ('*40Ar %', arar_age.rad40_percent),
        #                    ('IC', arar_age.ic_factor)
        #                    ]
        #                 ]
        #
        #    return summary

    #    def _get_signal_dicts(self):
    #        sig, base, blank = {}, {}, {}
    #        if self.arar_age:
    #            isos = self.arar_age.isotopes.values()
    ##            isos = [iso for iso in self.arar_age.isotopes.values()]
    #
    #            sig = dict([(v.name, v.uvalue) for v in isos])
    #            base = dict([(v.name, v.baseline.uvalue) for v in isos])
    #            blank = dict([(v.name, v.blank.uvalue) for v in isos])
    #        return sig, base, blank
    #
    #    def _make_display_ratios(self):
    #        cfb = self.correct_for_baseline
    #        cfbl = self.correct_for_blank
    ##         base = self.baselines
    ##         blank = self.blanks
    #        sig, base, blank = self._get_signal_dicts()
    #
    #        def factory(n, d, scalar=1):
    #            r = DisplayRatio(name='{}/{}'.format(n, d))
    #            try:
    #                sn = sig[n]
    #                sd = sig[d]
    #            except KeyError:
    #                return r
    #
    #            for ci, dd in ((cfb, base), (cfbl, blank)):
    #                if ci:
    #                    try:
    #                        sn -= dd[n]
    #                        sd -= dd[d]
    #                    except KeyError:
    #                        pass
    #            try:
    #                rr = (sn / sd) * scalar
    #                v, e = rr.nominal_value, rr.std_dev
    #            except ZeroDivisionError:
    #                v, e = 0, 0
    #            r.value = v
    #            r.error = e
    #
    #            return r
    #
    #        ratios = [('Ar40', 'Ar39'), ('Ar40', 'Ar36')]
    #        return [factory(*args) for args in ratios]

    #    def _make_display_signals(self):
    ##         sig = self.signals
    ##         base = self.baselines
    ##         blank = self.blanks
    ##         sig=dict([(k,v) ])
    #        sig, base, blank = self._get_signal_dicts()
    #        cfb = self.correct_for_baseline
    #        cfbl = self.correct_for_blank
    #        def factory(det, fi):
    #            iso = det.isotope
    #            if iso in sig:
    #                v = sig[iso]
    #            else:
    #                v = ufloat(0, 0)
    #
    #            if iso in base:
    #                bv = base[iso]
    #            else:
    #                bv = ufloat(0, 0)
    #
    #            if iso in blank:
    #                blv = blank[iso]
    #            else:
    #                blv = ufloat(0, 0)
    #
    #            iv = v
    #            if cfb:
    #                iv = iv - bv
    #
    #            if cfbl:
    #                iv = iv - blv
    #
    #            return DisplaySignal(isotope=iso,
    #                                 detector=det.name,
    #                                 fit=fi[0].upper(),
    #                                 intercept_value=iv.nominal_value,
    #                                 intercept_error=iv.std_dev,
    #                                 raw_value=v.nominal_value,
    #                                 raw_error=v.std_dev,
    #                                 baseline_value=bv.nominal_value,
    #                                 baseline_error=bv.std_dev,
    #                                 blank_value=blv.nominal_value,
    #                                 blank_error=blv.std_dev,
    #                                 )
    #
    #        return [factory(det, fi) for det, fi in zip(self.detectors, self.fits)]

    def _get_ncounts(self):
        return self._ncounts

    def _set_ncounts(self, v):
        self.info('{} set to terminate after {} counts'.format(self.plot_title, v))
        self._ncounts = v

    def _get_ncycles(self):
        return self._ncycles

    def _set_ncycles(self, v):
        self.info('{} set to terminate after {} ncycles'.format(self.plot_title, v))
        self._ncycles = v

    def _graph_factory(self):
        return StackedRegressionGraph(container_dict=dict(padding=5, bgcolor='gray',
                                                          stack_order=self.stack_order,
                                                          spacing=5),
                                      bind_index=False,
                                      use_data_tool=False,
                                      padding_bottom=35)


    def _get_isotopes(self):
        return [d.isotope for d in self.detectors]

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('isotope_graph, peak_center_graph')
    def _update_graphs(self):
        if self.isotope_graph and self.peak_center_graph:
            g, p = self.isotope_graph, self.peak_center_graph

            g.page_name = 'Isotopes'
            p.page_name = 'Peak Center'
            self.graphs = [g, p]

            #            self.graph_container.graphs = [g, p]

    def _plot_title_changed(self, new):
        self.graph_container.label = new

    @on_trait_change('isotope_graph:regression_results')
    def _update_display(self, new):
        if new:
            arar_age = self.arar_age

            for iso, reg in zip(self._plot_keys, new):
                if reg is None:
                    continue

                try:
                    vv = reg.predict(0)
                    ee = reg.predict_error(0)
                    if self.is_baseline:
                        arar_age.set_baseline(iso, (vv, ee))
                    else:
                        arar_age.set_isotope(iso, (vv, ee))

                except TypeError, e:
                    print 'type error', e
                    break
                except AssertionError, e:
                    print 'assertion error', e
                    continue
            else:
                if self.refresh_age:
                    arar_age.calculate_age()

                self.analysis_view.load_computed(arar_age, new_list=False)
                self.analysis_view.refresh_needed = True

                #===============================================================================
                # defaults
                #===============================================================================

    def _isotope_graph_default(self):
        return self._graph_factory()

    def _graph_container_default(self):
        self.isotope_graph.page_name = 'Isotopes'
        self.peak_center_graph.page_name = 'Peak Center'

        #        return GraphContainer(graphs=[self.graph, self.peak_center_graph])
        return GraphContainer(model=self)

    def _graphs_default(self):
        return [self.isotope_graph, self.peak_center_graph]

        #============= EOF =============================================
