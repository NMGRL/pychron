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
from traits.api import Str, List
from traitsui.api import VGroup, UItem, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.entry.entry_views.entry import BaseEntry, OKButton, STYLESHEET, SpacelessStr


class RepositoryIdentifierEntry(BaseEntry):
    tag = 'Repository Identifier'
    principal_investigator = Str
    principal_investigators = List
    value = SpacelessStr

    def _add_item(self):
        return self.dvc.add_repository(self.value, self.principal_investigator)

    def traits_view(self):
        # style_sheet='QLabel {font-size: 10px} QLineEdit {font-size: 10px}'

        a = VGroup(Item('value', label='Repository Name'),
                   Item('principal_investigator', editor=ComboboxEditor(name='principal_investigators')),
                   UItem('error_message', style='readonly', style_sheet=STYLESHEET))
        buttons = [OKButton(), 'Cancel']
        return self._new_view(a,
                              width=400,
                              title='Add {}'.format(self.tag),
                              buttons=buttons)
# ============= EOF =============================================
