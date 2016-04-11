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
from pyface.action.menu_manager import MenuManager
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int
from traitsui.api import View, Item, UItem, HGroup, VGroup, EnumEditor, TabularEditor, HSplit, Handler

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.directory_editor import myDirectoryEditor
from pychron.core.ui.text_editor import myTextEditor
from pychron.paths import paths


class CommitAdapter(TabularAdapter):
    columns = [('Commit', 'message'), ('Date', 'date')]
    font = '10'
    date_width = Int(100)
    def get_menu( self, object, trait, row, column ):
        return MenuManager(Action(name='Diff', action='on_diff'))

class CentralPaneHandler(Handler):
    def on_diff(self, info, obj):
        obj.diff_selected()


class WorkspaceCentralPane(TraitsTaskPane):
    def traits_view(self):
        info_grp = HGroup(UItem('selected_branch', editor=EnumEditor(name='branches')),
                          Item('path', style='readonly'))
        # Item('nanalyses', style='readonly')

        dir_grp = UItem('path', style='custom',
                        editor=myDirectoryEditor(root_path=paths.workspace_root_dir,
                                                 dclick_name='dclicked',
                                                 selected_name='selected',
                                                 root_path_name='path'))

        # top = Tabbed(VGroup(UItem('selected_text',
        # editor=myTextEditor()),
        #                     label='Text'),
        #              VGroup(UItem('selected_path_commits',
        #                           editor=TabularEditor(adapter=CommitAdapter())),
        #                     label='Commits'))

        right = VGroup(UItem('selected_text', editor=myTextEditor()),
                       VGroup(UItem('selected_path_commits', editor=TabularEditor(editable=False,
                                                                                  multi_select=True,
                                                                                  selected='selected_commits',
                                                                                  adapter=CommitAdapter())),
                              show_border=True, label='File Log'))

        bot = VGroup(UItem('commits',
                           editor=TabularEditor(editable=False,
                                                adapter=CommitAdapter())),
                     show_border=True,
                     label='Branch Log')
        left = VGroup(dir_grp, bot)

        return View(VGroup(info_grp,
                           HSplit(left,
                                  right)),
                    handler = CentralPaneHandler())


class WorkspaceControlPane(TraitsDockPane):
    name = 'Controls'

    def traits_view(self):
        return View()

        # ============= EOF =============================================



