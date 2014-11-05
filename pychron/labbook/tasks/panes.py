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
from traits.api import HasTraits, Button, Str, Int, Bool, Any, List
from traitsui.api import View, Item, UItem, HGroup, VGroup, TreeEditor, TreeNode
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import ListStrEditor, TabularEditor
from pychron.core.hierarchy import Hierarchy, FilePath, FilePathAdapter


class NotesBrowserPane(TraitsDockPane):
    name = 'Notes'
    id = 'pychron.labbook.browser'

    def traits_view(self):
        nodes = [TreeNode(node_for=[Hierarchy],
                          children='children',
                          auto_open=True,
                          # on_click=self.model._on_click,
                          label='name', ),
                 TreeNode(node_for=[FilePath],
                          label='name')]

        v = View(VGroup(
            HGroup(Item('chronology_visible',
                        label='View Chronology')),
            UItem('object.hierarchy.chronology',
                  editor=TabularEditor(adapter=FilePathAdapter()),
                  visible_when='chronology_visible'),
            UItem('hierarchy',
                  visible_when='not chronology_visible',
                  show_label=False,
                  editor=TreeEditor(
                      auto_open=1,
                      selected='selected_root',
                      dclick='dclicked',
                      nodes=nodes,
                      editable=False))))
        return v

# ============= EOF =============================================



