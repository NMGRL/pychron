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
from traits.api import HasTraits, Str, Bool, List, Button
from traitsui.api import View, UItem, TableEditor, HGroup, spring
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class NewBranchView(HasTraits):
    name = Str
    def traits_view(self):
        v=View(UItem('name'),
               kind='livemodal',
               buttons=['OK','Cancel'], title='New Branch')
        return v

class NewTagView(HasTraits):
    tag_name = Str
    branch = Str
    def traits_view(self):
        v=View(UItem('tag_name'),
               kind='livemodal',
               buttons=['OK','Cancel'], title='Tag Branch {}'.format(self.branch))
        return v


class Existing(HasTraits):
    name = Str
    recheckout =Bool

class ChooseReheckoutAnalysesView(HasTraits):
    existing=List
    toggle_recheckout = Button
    _toggle_recheckout_state = Bool

    def _toggle_recheckout_fired(self):
        s = self._toggle_recheckout_state
        self._toggle_recheckout_state = s = not s
        for e in self.existing:
            e.recheckout = s

    def get_analyses_to_checkout(self):
        return [e.name for e in self.existing if e.recheckout]

    def get_analyses_to_skip(self):
        return [e.name for e in self.existing if not e.recheckout]

    def __init__(self, existing, *args, **kw):
        self.existing = [Existing(name=os.path.splitext(n)[0]) for n in existing]
        super(ChooseReheckoutAnalysesView, self).__init__(*args, **kw)

    def traits_view(self):
        cols=[CheckboxColumn(name='recheckout',label='Recheckout'),
              ObjectColumn(name='name', editable=False)]
        editor=TableEditor(columns=cols, sortable=False)

        v=View(UItem('existing', editor=editor),
               HGroup(icon_button_editor('toggle_recheckout', 'tick', tooltip='Toggle recheckout for all analyses'),
                      spring),
               width=300,
               resizable=True,
               title='Choose analyses to recheckout',
               kind='livemodal',
               buttons=['OK','Cancel'])
        return v
#============= EOF =============================================



