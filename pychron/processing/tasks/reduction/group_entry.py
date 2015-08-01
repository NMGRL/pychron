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
from traits.api import HasTraits, Str, Property, List
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from pychron.envisage.browser.adapters import AnalysisAdapter


class ReductionAnalysisGroupEntry(HasTraits):
    name = Str
    items = List
    ritems = List
    analysis_type = Str
    ranalysis_type = Str
    analyses = Property

    def _get_analyses(self):
        return (self.items, self.analysis_type), (self.ritems, self.ranalysis_type)

    def set_items(self, ans):
        (items, at), (ritems, rat) = ans
        self.ranalysis_type = rat
        self.analysis_type = at

        self.items = items
        if ritems:
            self.ritems = ritems

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(Item('name', label='Analysis Group Name')),
                VGroup(
                    UItem('items', editor=TabularEditor(adapter=AnalysisAdapter(),
                                                        operations=['delete'])),
                    UItem('ritems', editor=TabularEditor(adapter=AnalysisAdapter(),
                                                         operations=['delete'])))),
            resizable=True,
            buttons=['OK', 'Cancel'],
            kind='livemodal',
            title='Analysis Group Entry')
        return v

# ============= EOF =============================================



