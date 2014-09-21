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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, Item, UItem, DirectoryEditor, HGroup, VGroup, ListStrEditor, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.paths import paths


class WorkspaceCentralPane(TraitsTaskPane):
    def traits_view(self):
        return View(VGroup(HGroup(UItem('selected_branch', editor=EnumEditor(name='branches')),
                                  Item('path', style='readonly')),
                          Item('nanalyses', style='readonly'),
                    HGroup(UItem('path', style='custom',
                          editor=DirectoryEditor(root_path=paths.workspace_root_dir,
                                                 dclick_name='dclicked',
                                                 root_path_name='path')),
                        VGroup(UItem('selected_path_commits', editor=ListStrEditor()),
                               UItem('commits', editor=ListStrEditor())))))


class WorkspaceControlPane(TraitsDockPane):
    name = 'Controls'

    def traits_view(self):
        return View()

#============= EOF =============================================



