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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from pyface.action.menu_manager import MenuManager
from traitsui.menu import Action
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import HasTraits, Str, Instance, Event, Int, Bool, Any, Float, Property, on_trait_change, List
from traitsui.api import View, UItem, Item, HGroup, VGroup, TreeNode, Handler
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.updater.tasks.actions import CheckForUpdatesAction, ManageBranchAction
from pychron.envisage.resources import icon
from pychron.core.ui.tree_editor import TreeEditor


class AdditionTreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        return icon('tick' if obj.enabled else 'cancel')


class ViewModel(HasTraits):
    task_extensions = List
    enabled = True

    def update(self):
        pass

    def get_te_model(self, tid):
        return next((te for te in self.task_extensions if te.id == tid), None)


class TaskExtensionModel(HasTraits):
    additions = List
    id = Str
    all_enabled = Bool
    enabled = True


class AdditionModel(HasTraits):
    model = SchemaAddition
    name = Str
    enabled = Bool


class EEHandler(Handler):
    def set_enabled(self, info, obj):
        for si in info.object.selected:
            si.enabled = True
        info.object.refresh_all_needed = True
        self._finish_toggle_enable(info)

    def set_disabled(self, info, obj):
        for si in info.object.selected:
            si.enabled = False
        info.object.refresh_all_needed = True
        self._finish_toggle_enable(info)

    def set_all_enabled(self, info, obj):
        self._set_all(obj, True)
        info.object.refresh_all_needed = True
        self._finish_toggle_enable(info)

    def set_all_disabled(self, info, obj):
        self._set_all(obj, False)
        self._finish_toggle_enable(info)

    def _finish_toggle_enable(self, info):
        info.object.refresh_all_needed = True
        info.object.update()

    def _set_all(self, te, v):
        for a in te.additions:
            a.enabled = v
        te.all_enabled = v


class EditExtensionsView(HasTraits):
    view_model = Instance(ViewModel, ())
    refresh_all_needed = Event
    selected = List
    dclicked = Event

    def update(self):
        self.view_model.update()

    def add_additions(self, tid, name, a):
        adds = []
        for ai in a:
            adds.append(AdditionModel(model=ai,
                                      name=ai.factory.dname))
        te = self.view_model.get_te_model(tid)
        if te is None:
            te = TaskExtensionModel(name=name, id=tid, additions=adds)
            self.view_model.task_extensions.append(te)
        else:
            te.additions.extend(adds)


def edit_task_extensions(available_additions):
    e = EditExtensionsView()
    e.add_additions('pychron.update', 'Update', available_additions)

    nodes = [TreeNode(node_for=[ViewModel],
                      icon_open='',
                      children='task_extensions'),
             TreeNode(node_for=[TaskExtensionModel],
                      auto_open=True,
                      children='additions',
                      label='name',
                      menu=MenuManager(Action(name='Enable All',
                                              visible_when='not object.all_enabled',
                                              action='set_all_enabled'),
                                       Action(name='Disable All',
                                              visible_when='object.all_enabled',
                                              action='set_all_disabled'))),
             AdditionTreeNode(node_for=[AdditionModel],
                              label='name',
                              menu=MenuManager(Action(name='Enable',
                                                      action='set_enabled',
                                                      visible_when='not object.enabled'),
                                               Action(name='Disable',
                                                      visible_when='object.enabled',
                                                      action='set_disabled')))]
    AView = View(UItem('view_model',
                       editor=TreeEditor(nodes=nodes,
                                         selection_mode='extended',
                                         selected='selected',
                                         dclick='dclicked',
                                         show_disabled=True,
                                         refresh_all_icons='refresh_all_needed',
                                         editable=False)),
                 handler=EEHandler(),
                 kind='livemodal')

    info = e.configure_traits(view=AView)
    # info = e.edit_traits(view=AView)
    if info.result:
        return confirm() == YES


if __name__ == '__main__':
    a = [SchemaAddition(id='pychron.update.check',
                        factory=CheckForUpdatesAction),
         SchemaAddition(id='pychron.update.check',
                        factory=ManageBranchAction)
    ]
    edit_task_extensions(a)
# ============= EOF =============================================



