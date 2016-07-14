# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
from traits.api import HasTraits, Instance, List, Str, Any, Property, Int
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin


class SelectorAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Analysis Time', 'rundate'),
               ('Irradiation', 'irradiation_info'),
               ('Mass Spec.', 'mass_spectrometer'),
               ('Type', 'analysis_type'),
               ('Project', 'project'),
               ('Measurement', 'meas_script_name'),
               ('Extraction', 'extract_script_name')]

    font = '10'
    rid_text = Property
    mass_spectrometer_width = Int(90)
    analysis_type_width = Int(100)
    rundate_width = Int(120)

    meas_script_width = Int(120)
    extract_script_width = Int(90)


class ReferenceAnalysisSelector(HasTraits, ColumnSorterMixin):
    db = Instance('pychron.dvc.dvc.DVC')
    title = Str
    items = List
    selected = Any
    scroll_to_row = Int

    def init(self, title, ans):
        self.items = ans
        self.title = title
        self.scroll_to_row = len(ans) - 1
        self.selected = ans[-1]

    def traits_view(self):
        g = UItem('items', editor=TabularEditor(adapter=SelectorAdapter(),
                                                scroll_to_row='scroll_to_row',
                                                column_clicked='column_clicked',
                                                editable=False,
                                                selected='selected'))
        v = View(g, title=self.title,
                 width=750,
                 buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
