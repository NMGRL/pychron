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
from traits.api import Str
from traitsui.api import Item, VGroup, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.entry_views.entry import BaseEntry


class ExperimentIdentifierEntry(BaseEntry):
    tag = 'Experiment Identifier'
    name = Str
    description = Str

    def _add_item(self):
        return self.dvc.add_experiment(self.name, description=self.description)

    def traits_view(self):
        return self._new_view(Item('name'),
                              VGroup(UItem('description', style='custom'),
                                     show_border=True, label='Description (optional)'),
                              title='New Experiment Identifier')
# ============= EOF =============================================
