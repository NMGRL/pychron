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
from pychron.core.helpers.filetools import to_bool
from pychron.core.ui import set_qt

set_qt()

from pychron.paths import paths
from pychron.processing.tasks.actions.processing_actions import RecallAction


# ============= enthought library imports =======================
from pyface.action.menu_manager import MenuManager
from traitsui.menu import Action
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import HasTraits, Str, Instance, Event, Int, Bool, Any, Float, Property, on_trait_change, List
from traitsui.api import View, UItem, Item, HGroup, VGroup, TreeNode, Handler
# ============= standard library imports ========================
import yaml
# ============= local library imports  ==========================
from pychron.updater.tasks.actions import CheckForUpdatesAction, ManageBranchAction
from pychron.envisage.resources import icon
from pychron.core.ui.tree_editor import TreeEditor


class AdditionTreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        return icon('tick' if obj.enabled else 'cancel')


class TETreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        return icon('package-green')


class ViewModel(HasTraits):
    task_extensions = List
    enabled = True

    def load(self):
        p = paths.task_extensions_file
        with open(p, 'r') as rfile:
            yl = yaml.load(rfile)
            for te in self.task_extensions:
                yd = next((d for d in yl if d['plugin_id'] == te.id), None)
                # print yd, te.id, te
                if yd:
                    for ai in yd['actions']:
                        action, enabled = ai.split(',')
                        tt = next((ta for ta in te.additions if ta.model.id == action), None)
                        if tt:
                            tt.enabled = to_bool(enabled)

    def dump(self):
        p = paths.task_extensions_file
        obj = [te.dump() for te in self.task_extensions]
        with open(p, 'w') as wfile:
            yaml.dump(obj, wfile)

    def get_te_model(self, tid):
        return next((te for te in self.task_extensions if te.id == tid), None)


class TaskExtensionModel(HasTraits):
    additions = List
    id = Str
    all_enabled = Bool
    enabled = True

    def dump(self):
        return {'plugin_id': self.id, 'actions': ['{}, {}'.format(a.model.id, a.enabled) for a in self.additions]}


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

    def _set_all(self, te, v):
        for a in te.additions:
            a.enabled = v
        te.all_enabled = v


class EditExtensionsView(HasTraits):
    view_model = Instance(ViewModel, ())
    refresh_all_needed = Event
    selected = List
    dclicked = Event

    def _dclicked_fired(self):
        s = self.selected[0]
        s.enabled = not s.enabled
        self.refresh_all_needed = True

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
            ids = [a.model.id for a in te.additions]
            adds = [ai for ai in adds if ai.model.id not in ids]
            te.additions.extend(adds)


def edit_task_extensions(ts):
    e = EditExtensionsView()
    for args in ts:
        e.add_additions(*args)
    e.view_model.load()

    nodes = [TreeNode(node_for=[ViewModel],
                      icon_open='',
                      children='task_extensions'),
             TETreeNode(node_for=[TaskExtensionModel],
                        # auto_open=True,
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
                 title='Edit UI',
                 width=500,
                 height=700,
                 resizable=True,
                 handler=EEHandler(),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')

    # info = e.configure_traits(view=AView)
    info = e.edit_traits(view=AView)
    if info.result:
        e.view_model.dump()
        return confirm(None, 'Restart?') == YES


if __name__ == '__main__':
    from traits.api import Button

    class Demo(HasTraits):
        test = Button
        traits_view = View('test')

        def _test_fired(self):
            a = [('pychron.update', 'Update', [SchemaAddition(id='pychron.update.check_for_updates',
                                                              factory=CheckForUpdatesAction),
                                               SchemaAddition(id='pychron.update.manage_branch',
                                                              factory=ManageBranchAction)]),
                 ('pychron.recall', 'Recall', [SchemaAddition(id='pychron.recall',
                                                              factory=RecallAction)])]
            edit_task_extensions(a)

    d = Demo()
    d.configure_traits()
# ============= EOF =============================================



