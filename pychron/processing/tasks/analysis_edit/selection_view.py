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
import os

from traits.api import HasTraits, List, Any, Int
from traitsui.api import View, Item, UItem, CheckListEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin


class ReferenceSelectionView(HasTraits, PersistenceMixin):
    atypes = List(['Blank Unknown'])
    available_atypes = List(['Blank Unknown', 'Blank Air', 'Blank Cocktail', 'Air', 'Cocktail'])

    hours = Int
    pattributes = ('atypes','hours')
    persistence_path = os.path.join(paths.hidden_dir, 'reference_selection')

    @property
    def analysis_types(self):
        return map(lambda x: x.lower().replace(' ', '_'), self.atypes)

    def traits_view(self):
        v = View(UItem('atypes',
                       style='custom',
                       editor=CheckListEditor(name='available_atypes', cols=10)),
                 Item('hours'),
                 buttons=['OK', 'Cancel'],
                 title='Select Analysis Types',
                 resizable=True)
        return v


class AnalysisAdapter(TabularAdapter):
    font = '10'
    columns = [('Run ID', 'record_id'),
               ('Date', 'rundate')]
    ref = Any

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if self.item == self.ref:
            color = 'gray'
        return color


class AnalysisSelectionView(HasTraits):
    analyses = List
    selected = List
    ref = Any

    def traits_view(self):
        v = View(UItem('analyses', editor=TabularEditor(adapter=AnalysisAdapter(ref=self.ref),
                                                        multi_select=True,
                                                        selected='selected',
                                                        editable=False)),
                 title='Select Analyses',
                 buttons=['OK', 'Cancel'],
                 resizable=True,
                 width=500)
        return v

# ============= EOF =============================================



