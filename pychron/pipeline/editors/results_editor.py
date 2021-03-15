# ===============================================================================
# Copyright 2015 Jake Ross
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
from itertools import groupby
from operator import attrgetter

from enable.component_editor import ComponentEditor
from numpy import poly1d, linspace
from traits.api import Int, Property, List, Instance, Event, Bool, Button, List
from traitsui.api import View, UItem, TabularEditor, VGroup, HGroup, Item, Tabbed
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.envisage.tasks.base_editor import BaseTraitsEditor, grouped_name
from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.options.layout import filled_grid
from pychron.options.options_manager import RegressionSeriesOptionsManager, OptionsController
from pychron.options.views.views import view
from pychron.pipeline.plot.figure_container import FigureContainer
from pychron.pipeline.plot.models.regression_series_model import RegressionSeriesModel
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, LIGHT_RED


class IsoEvolutionResultsAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('UUID', 'display_uuid'),
               ('Isotope', 'isotope'),
               ('Fit', 'fit'),
               ('N', 'nstr'),
               ('Intercept', 'intercept_value'),
               (PLUSMINUS_ONE_SIGMA, 'intercept_error'),
               ('%', 'percent_error'),
               ('Regression', 'regression_str')]
    font = '10'
    record_id_width = Int(80)
    isotope_width = Int(50)
    fit_width = Int(80)
    intercept_value_width = Int(120)
    intercept_error_width = Int(80)
    percent_error_width = Int(60)

    intercept_value_text = Property
    intercept_error_text = Property
    percent_error_text = Property

    def get_tooltip(self, obj, trait, row, column):
        item = getattr(obj, trait)[row]

        return item.tooltip

    def get_bg_color(self, obj, trait, row, column=0):
        if not obj.display_only_bad:
            item = getattr(obj, trait)[row]
            if not item.goodness:
                return LIGHT_RED

    def _get_intercept_value_text(self):
        return self._format_number('intercept_value')

    def _get_intercept_error_text(self):
        return self._format_number('intercept_error')

    def _get_percent_error_text(self):
        return self._format_number('percent_error', n=3)

    def _format_number(self, attr, **kw):
        if self.item.record_id:
            v = getattr(self.item, attr)
            r = floatfmt(v, **kw)
        else:
            r = ''
        return r


class IsoEvolutionResultsEditor(BaseTraitsEditor, ColumnSorterMixin):
    results = List
    adapter = Instance(IsoEvolutionResultsAdapter, ())
    dclicked = Event
    display_only_bad = Bool
    view_bad_button = Button('View Flagged')
    view_selected_button = Button('View Selected')
    selected = List
    graph = Instance(Graph)

    def __init__(self, results, fits, *args, **kw):
        super(IsoEvolutionResultsEditor, self).__init__(*args, **kw)

        na = grouped_name([r.identifier for r in results if r.identifier])
        self.name = 'IsoEvo Results {}'.format(na)

        self.oresults = self.results = results
        self.fits = fits
        self._make_graph()
        # self.results = sorted(results, key=lambda x: x.goodness)

    def _make_graph(self):
        results = self.results
        fits = self.fits
        # a = 0.0003
        # b = 0.5
        # c = 0.00005
        # d = 0.015
        isos = len({r.isotope for r in results})
        g = Graph(container_dict={'kind': 'g',
                                  'shape': filled_grid(isos)})
        key = attrgetter('isotope')
        for i, (iso, gg) in enumerate(groupby(sort_isotopes(results, key=key),
                                              key=key)):
            fit = next((fi for fi in fits if fi.name == iso))
            x, y = zip(*((r.intercept_value, r.intercept_error) for r in gg))
            xx = linspace(min(x), max(x))

            yy = fit.smart_filter_values(xx)
            g.new_plot()
            g.new_series(x, y, plotid=i, type='scatter', marker='plus')
            g.new_series(xx, yy, plotid=i)
            g.set_x_title('Intensity', plotid=i)
            g.set_y_title('Error', plotid=i)
            g.set_plot_title(iso, plotid=i)

        self.graph = g

    def _view_selected_button_fired(self):
        ans = list({r.analysis for r in self.selected})

        self._show_results(ans)

    def _view_bad_button_fired(self):
        ans = list({r.analysis for r in self.oresults if not r.goodness})
        self._show_results(ans)

    def _show_results(self, ans):

        c = FigureContainer()
        pom = RegressionSeriesOptionsManager()
        names = list({k for a in ans for k in a.isotope_keys})
        pom.set_names(names)
        pom.selected = 'multiregression'

        info = OptionsController(model=pom).edit_traits(view=view('Regression Options'),
                                                        kind='livemodal')
        if info.result:
            m = RegressionSeriesModel(analyses=ans, plot_options=pom.selected_options)
            c.model = m
            v = View(UItem('component',
                           style='custom',
                           editor=ComponentEditor()),
                     title='Regression Results',
                     width=0.90,
                     height=0.75,
                     resizable=True)

            c.edit_traits(view=v)

    def _display_only_bad_changed(self, new):
        if new:
            self.results = [r for r in self.results if not r.goodness]
        else:
            self.results = self.oresults

    def _dclicked_fired(self, new):
        if new:
            result = new.item
            result.analysis.show_isotope_evolutions((result.isotope,))

    def traits_view(self):
        filter_grp = HGroup(Item('display_only_bad', label='Show Flagged Only'),
                            UItem('view_bad_button'),
                            UItem('view_selected_button'))
        ggrp = VGroup(UItem('graph', style='custom'),
                      label='Graph')
        tgrp = VGroup(filter_grp,
                      UItem('results', editor=TabularEditor(adapter=self.adapter,
                                                            editable=False,
                                                            multi_select=True,
                                                            selected='selected',
                                                            column_clicked='column_clicked',
                                                            dclicked='dclicked')),
                      label='Table')
        v = View(Tabbed(ggrp, tgrp))
        return v

# ============= EOF =============================================
