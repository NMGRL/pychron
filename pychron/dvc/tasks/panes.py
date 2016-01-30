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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int, Property
from traitsui.api import View, UItem, VGroup, ListStrEditor, TabularEditor, EnumEditor
from traitsui.tabular_adapter import TabularAdapter


# ============= standard library imports ========================
# ============= local library imports  ==========================


class CommitAdapter(TabularAdapter):
    columns = [('ID', 'hexsha'),
               ('Date', 'date'),
               ('Message', 'message'),
               ('Author', 'author'),
               ('Email', 'email'),
               ]
    hexsha_width = Int(80)
    message_width = Int(300)
    date_width = Int(120)
    author_width = Int(100)

    font = '10'
    hexsha_text = Property

    def _get_hexsha_text(self):
        return self.item.hexsha[:8]


class RepoCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(UItem('branch',
                              editor=EnumEditor(name='branches')),
                        UItem('commits',
                              editor=TabularEditor(adapter=CommitAdapter(),
                                                   selected='selected_commit'))))
        return v


class SelectionPane(TraitsDockPane):
    id = 'pychron.repo.selection'
    name = 'Repositories'

    def traits_view(self):
        origin_grp = VGroup(UItem('repository_names',
                                  editor=ListStrEditor(selected='selected_repository_name',
                                                       editable=False)),
                            show_border=True, label='Origin')
        local_grp = VGroup(UItem('local_names',
                                 editor=ListStrEditor(selected='selected_local_repository_name',
                                                      editable=False)),
                           show_border=True, label='Local')

        v = View(VGroup(local_grp, origin_grp))
        return v

# ============= EOF =============================================
