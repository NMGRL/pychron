#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, Item, UItem, TableEditor, HGroup, EnumEditor, HSplit, InstanceEditor, VGroup, spring

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn


class VCSCentralPane(TraitsTaskPane):
    def traits_view(self):
        cols = [CheckboxColumn(name='use'),
                ObjectColumn(name='name', editable=False)]
        editor = TableEditor(columns=cols,
                             selected='selected_diff',
                             sortable=False
                             )

        v = View(
            VGroup(
                HGroup(Item('selected_repository', editor=EnumEditor(name='repositories'),
                            label='Repo'), ),
                HSplit(UItem('diffs', editor=editor),
                       UItem('selected_diff', style='custom', editor=InstanceEditor())),
                VGroup(
                    HGroup(spring, UItem('prev_commit_message', editor=EnumEditor(name='prev_commit_messages'))),
                    UItem('commit_message', style='custom'), label='Commit', show_border=True)),
            )
        return v

#============= EOF =============================================

