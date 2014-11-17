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
from traitsui.api import View, Item, UItem, HGroup, VGroup, TreeEditor, TreeNode
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor, InstanceEditor
from traitsui.group import VSplit
from traitsui.item import spring
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.hierarchy import Hierarchy, FilePath, FilePathAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.git_archive.history import CommitAdapter


class LabelTabularAdapter(TabularAdapter):
    columns = [('Label', 'text')]

    def get_bg_color(self, object, trait, row, column=0):
        c = 'white'
        cstr = self.item.color
        if self.item.active:
            c = '#{}'.format(cstr[:-2])

        # print 'get bg color', self.item.text, self.item.active, c
        return c

    def get_text_color(self, obj, trait, row, column=0):

        item = getattr(obj, trait)[row]

        if item.active:
            r = item.color[:2]
            g = item.color[2:4]
            b = item.color[4:6]
            s = sum((int(r, 16), int(g, 16), int(b, 16)))
            c = 'white' if s < 256 else 'black'
        else:
            c = '#{}'.format(item.color[:-2])

        return c


class LabelPane(TraitsDockPane):
    name = 'Labels'
    id = 'pychron.labbook.labels'

    def traits_view(self):
        v = View(UItem('labels', editor=TabularEditor(editable=False,
                                                      selected='selected',
                                                      multi_select=True,
                                                      dclicked='dclick',
                                                      refresh='refresh_needed',
                                                      adapter=LabelTabularAdapter())))
        return v


class FileHistoryPane(TraitsDockPane):
    name = 'File History'
    id = 'pychron.labbook.file_history'

    def traits_view(self):
        v = View(VGroup(
            HGroup(spring, Item('limit')),
            VSplit(UItem('items',
                         height=0.75,
                         editor=TabularEditor(adapter=CommitAdapter(),
                                              multi_select=True,
                                              editable=False,
                                              selected='selected')),
                   UItem('selected_commit',
                         editor=InstanceEditor(),
                         height=0.25,
                         style='custom')),
            HGroup(spring, icon_button_editor('diff_button', 'edit_diff',
                                              enabled_when='diffable'),
                   UItem('checkout_button', enabled_when='checkoutable'))))
        return v


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
                        label='View Chronology'),
                   icon_button_editor('filter_by_date_button', 'calendar'),
                   UItem('date_filter')),
            HGroup(Item('filter_hierarchy_str',
                        label='Name Filter')),
            UItem('object.hierarchy.chronology',
                  editor=TabularEditor(editable=False,
                                       selected='selected_root',
                                       dclicked='dclicked',
                                       adapter=FilePathAdapter()),
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



