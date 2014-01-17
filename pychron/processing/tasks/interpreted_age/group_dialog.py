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
from traits.api import HasTraits, List, Any, Str, Int, Date
from traitsui.api import View, Item, TabularEditor, UItem, HGroup, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.browser.adapters import ProjectAdapter


class GroupAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Date','create_date')]


class GroupDialog(HasTraits):
    name = Str
    projects = List
    selected_project = Any


class SaveGroupDialog(GroupDialog):
    def traits_view(self):
        v = View(VGroup(HGroup(Item('name')),
                        UItem('projects',
                              editor=TabularEditor(adapter=ProjectAdapter(),
                                                   selected='selected_project',
                                                   editable=False))),
                 buttons=['OK', 'Cancel'], resizable=True,
                 title='Save Interpreted Age Group',
                 width=300)
        return v


class IAGroup(HasTraits):
    name = Str
    project = Str
    id = Int
    create_date=Date

class SelectionGroupDialog(GroupDialog):
    groups = List
    db = Any
    selected_groups = List
    title=Str

    def get_selected_ids(self):
        return [gi.id for gi in self.selected_groups]

    def _selected_project_changed(self):
        self.groups = []
        if self.selected_project:
            gs = []
            db = self.db
            with db.session_ctx():
                hists = db.get_interpreted_age_groups(self.selected_project.name)
                for hi in hists:
                    gs.append(IAGroup(name=hi.name,
                                      project=self.selected_project.name,
                                      id=int(hi.id),
                                      create_date=hi.create_date))
            self.groups = gs

    def traits_view(self):
        v = View(VGroup(
            UItem('projects',
                  editor=TabularEditor(adapter=ProjectAdapter(),
                                       selected='selected_project',
                                       editable=False)),
            UItem('groups',
                  editor=TabularEditor(adapter=GroupAdapter(),
                                       selected='selected_groups',
                                       multi_select=True,
                                       editable=False))),
                 buttons=['OK', 'Cancel'], resizable=True,
                 title=self.title,
                 width=300)
        return v


class OpenGroupDialog(SelectionGroupDialog):
    title='Open Interpreted Age Group'


class DeleteGroupDialog(SelectionGroupDialog):
    title='Delete Interpreted Age Groups'

#============= EOF =============================================

