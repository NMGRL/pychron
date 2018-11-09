# ===============================================================================
# Copyright 2018 ross
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
from traits.api import List, Instance, Int, Any
from traitsui.api import View, UItem, TabularEditor, VSplit
from traitsui.tabular_adapter import TabularAdapter

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.envisage.tasks.base_editor import BaseTraitsEditor, grouped_name
from pychron.graph.stacked_regression_graph import StackedRegressionGraph


class DefineEquilibrationResultsAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Isotope', 'isotope'),
               ('Equilibration Time', 'equilibration_time')]
    record_id_width = Int(100)
    isotope_width = Int(75)


class DefineEquilibrationResultsEditor(BaseTraitsEditor, ColumnSorterMixin):
    results = List
    adapter = Instance(DefineEquilibrationResultsAdapter, ())
    # dclicked = Event
    graph = Instance(StackedRegressionGraph)
    selected = Any

    def __init__(self, results, *args, **kw):
        super(DefineEquilibrationResultsEditor, self).__init__(*args, **kw)

        na = grouped_name([r.identifier for r in results if r.identifier])
        self.name = 'Define Eq. Results {}'.format(na)

        self.results = results

    def _selected_changed(self, new):
        if new:
            self.graph = new.analysis.get_isotope_evolutions((new.isotope,),
                                                             load_data=False,
                                                             show_equilibration=True)
    # def _dclicked_fired(self, new):
    #     if new:
    #         result = new.item
    #         result.analysis.show_isotope_evolutions((result.isotope,),
    #                                                 load_data=False,
    #                                                 show_equilibration=True)

    def traits_view(self):
        v = View(VSplit(UItem('results', editor=TabularEditor(adapter=self.adapter,
                                                              editable=False,
                                                              multi_select=False,
                                                              selected='selected',
                                                              column_clicked='column_clicked',
                                                              # dclicked='dclicked'
                                                              )),
                        UItem('graph', style='custom', height=600))
                 )
        return v
# ============= EOF =============================================
