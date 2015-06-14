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
from traits.api import Int
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, VGroup, ListStrEditor, TabularEditor, EnumEditor
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================


class CommitAdapter(TabularAdapter):
    columns = [('Message', 'message'),
               ('Date', 'date'),
               ('Author', 'author'),
               ('Email', 'email'),
               ]
    message_width = Int(300)
    font = '10'


class RepoCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(UItem('selected_repository_name', style='readonly'),
                        UItem('branch',
                              editor=EnumEditor(name='branches')),
                        UItem('commits',
                              editor=TabularEditor(adapter=CommitAdapter(),
                                                   selected='selected_commit'))))
        return v


class SelectionPane(TraitsDockPane):
    id = 'pychron.repo.selection'
    name = 'Repositories'

    def traits_view(self):
        v = View(VGroup(UItem('repository_names',
                              editor=ListStrEditor(selected='selected_repository_name',
                                                   editable=False)),
                        UItem('local_names',
                              editor=ListStrEditor(selected='selected_local_repository_name',
                                                   editable=False))))
        return v

# ============= EOF =============================================
