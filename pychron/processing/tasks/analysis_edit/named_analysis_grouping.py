#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Str, List, Property, Button, Any, Event
from traitsui.api import View, Item, HGroup, UItem, VGroup, spring

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.editors import TabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.icon_button_editor import icon_button_editor

from pychron.processing.tasks.browser.panes import AnalysisAdapter, AnalysisGroupAdapter


class AnalysisGroupEntry(HasTraits):
    name = Str
    items = List
    analyses = Property
    analysis_type = Str

    def _get_analyses(self):
        return ((self.items, self.analysis_type),)

    def set_items(self, ans):
        items, at = ans[0]
        self.items = items
        self.analysis_type = at

    def traits_view(self):
        v = View(
            HGroup(Item('name', label='Analysis Group Name')),
            UItem('items', editor=TabularEditor(adapter=AnalysisAdapter())),
            resizable=True,
            buttons=['OK', 'Cancel'],
            kind='livemodal',
            title='Analysis Group Entry')
        return v


class AnalysisGroupDelete(HasTraits):
    groups = List
    delete_button = Button
    selected = List
    selected_projects = List
    task = Any
    refresh = Event

    def _selected_projects_changed(self):
        self.groups = self.task.get_analysis_groups(self.selected_projects)

    def _delete_button_fired(self):
        db = self.task.manager.db
        names = '\n'.join(['- {}'.format(si.name) for si in self.selected])
        if self.task.manager.confirmation_dialog(
                'Are you sure you want to delete?\n{}\nThis action is nonreversible'.format(names)):
            with db.session_ctx():
                for si in self.selected:
                    db.delete_analysis_group(si.id)
                    self.groups.remove(si)
            self.refresh = True

    def traits_view(self):
        v = View(VGroup(
            UItem('projects', editor=TabularEditor(adapter=ProjectAdapter(),
                                                   multi_select=True,
                                                   selected='selected_projects')),
            HGroup(icon_button_editor('delete_button', 'delete',
                                      tooltip='Remove the selected analysis groups from the database',
                                      enabled_when='selected'),
                   spring),
            UItem('groups',
                  editor=TabularEditor(adapter=AnalysisGroupAdapter(),
                                       multi_select=True,
                                       refresh='refresh',
                                       selected='selected'))),
                 resizable=True,
                 width=500,

                 title='Delete Analysis Group',
                 buttons=['OK', 'Cancel'])
        return v

#============= EOF =============================================
