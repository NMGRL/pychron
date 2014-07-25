# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Instance, List, Property
from traitsui.api import View, UItem, TabularEditor
# ============= standard library imports ========================
from numpy import array
from uncertainties import nominal_value
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt

from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor


class ResultsAdapter(TabularAdapter):
    columns = [('Identifier', 'identifier'),
               ('Min (Ma)', 'mi'),
               ('Max (Ma)', 'ma'),
               ('Spread (Ma)', 'spread'),
               ('Std.', 'std')]

    mi_text = Property
    ma_text = Property
    spread_text = Property
    std_text = Property

    def _get_mi_text(self):
        return floatfmt(self.item.mi)

    def _get_ma_text(self):
        return floatfmt(self.item.ma)

    def _get_spread_text(self):
        return floatfmt(self.item.spread)

    def _get_std_text(self):
        return floatfmt(self.item.std)

class ResultRecord(object):
    ma = 0
    mi = 0
    spread = 0
    std = 0
    identifier = ''

    def __init__(self, records):
        ages = array([nominal_value(ai.age) for ai in records])
        self.mi = min(ages)
        self.ma = max(ages)

        self.std = ages.std()

        self.identifier = records[0].identifier
        self.spread = self.ma - self.mi


class PermutatorResultsView(HasTraits):
    editor = Instance(GraphEditor)
    results = List

    def append_results(self, records):
        self.results.append(ResultRecord(records))

    def traits_view(self):
        v = View(UItem('editor', style='custom'),
                 UItem('results', editor=TabularEditor(adapter=ResultsAdapter())),
                 width=700,
                 height=600)
        return v

# ============= EOF =============================================



