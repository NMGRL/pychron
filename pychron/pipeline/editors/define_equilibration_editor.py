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
from traits.api import List, Instance, Int, Any, Event, Bool
from traitsui.api import View, UItem, TabularEditor, VSplit, VGroup, HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor, grouped_name
from pychron.graph.graph import Graph


class DefineEquilibrationResultsAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('UUID', 'display_uuid'),
               ('Equilibration Times', 'equilibration_times')]
    record_id_width = Int(100)


class DefineEquilibrationResultsEditor(BaseTraitsEditor, ColumnSorterMixin):
    results = List
    adapter = Instance(DefineEquilibrationResultsAdapter, ())
    # dclicked = Event
    graph = Instance(Graph)
    selected = Any
    next_button = Event
    previous_button = Event
    next_enabled = Bool
    previous_enabled = Bool

    options = Any

    def __init__(self, results, *args, **kw):
        super(DefineEquilibrationResultsEditor, self).__init__(*args, **kw)

        na = grouped_name([r.identifier for r in results if r.identifier])
        self.name = 'Define Eq. Results {}'.format(na)

        self.results = results
        self.selected = results[0]

    def _next_button_fired(self):
        self._select(1)

    def _previous_button_fired(self):
        self._select(-1)

    def _select(self, direction):
        idx = 0
        if self.selected:
            idx = self.results.index(self.selected)
        try:
            self.selected = self.results[idx + direction]
        except IndexError:
            pass

    def _selected_changed(self, new):
        if new:
            self.graph = new.analysis.get_isotope_evolutions(new.isotopes,
                                                             load_data=False,
                                                             show_equilibration=True,
                                                             ncols=self.options.ncols,
                                                             show_statistics=self.options.show_statistics,
                                                             scale_to_equilibration=True)
            idx = self.results.index(new)
            if idx == len(self.results) - 1:
                self.next_enabled = False
                self.previous_enabled = True
            elif idx == 0:
                self.next_enabled = True
                self.previous_enabled = False
            else:
                self.next_enabled = True
                self.previous_enabled = True

    def traits_view(self):
        v = View(VSplit(VGroup(HGroup(icon_button_editor('previous_button', 'arrow_left',
                                                         enabled_when='previous_enabled'),
                                      icon_button_editor('next_button', 'arrow_right',
                                                         enabled_when='next_enabled')),

                               UItem('results', editor=TabularEditor(adapter=self.adapter,
                                                                     editable=False,
                                                                     multi_select=False,
                                                                     selected='selected',
                                                                     column_clicked='column_clicked',
                                                                     # dclicked='dclicked'
                                                                     ))),
                        UItem('graph', style='custom', height=600)))
        return v
# ============= EOF =============================================
