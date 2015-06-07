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
from traits.api import Int, Property, List, Instance
from traitsui.api import View, UItem, TabularEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.pychron_constants import PLUSMINUS_SIGMA


class IsoEvolutionResultsAdapter(TabularAdapter):
    columns = [('RunID','record_id'), ('Isotope','isotope'), ('Fit', 'fit'),
               ('Intercept','intercept_value'),
               (PLUSMINUS_SIGMA,'intercept_error')]
    record_id_width = Int(80)
    isotope_width = Int(50)
    fit_width = Int(80)
    intercept_value_width = Int(120)
    intercept_error_width = Int(80)

    intercept_value_text = Property
    intercept_error_text = Property

    def _get_intercept_value_text(self):
        return self._format_number('intercept_value')

    def _format_number(self, attr):
        if self.item.record_id:
            v = getattr(self.item, attr)
            r = floatfmt(v)
        else:
            r = ''
        return r

    def _get_intercept_error_text(self):
        return self._format_number('intercept_error')


class IsoEvolutionResultsEditor(BaseTraitsEditor):
    results = List
    adapter = Instance(IsoEvolutionResultsAdapter, ())

    def __init__(self, results, *args, **kw):
        super(IsoEvolutionResultsEditor, self).__init__(*args, **kw)
        a = results[0]

        na = self._grouped_name([r.identifier for r in results if r.identifier])
        self.name = 'IsoEvo Results {}'.format(na)

        self.results = results

    def traits_view(self):
        v = View(UItem('results', editor=TabularEditor(adapter=self.adapter,
                                                       editable=False)))
        return v
# ============= EOF =============================================



