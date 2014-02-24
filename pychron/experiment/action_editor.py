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
import yaml

from pychron.core.ui import set_qt

set_qt()


#============= enthought library imports =======================
import os
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, List, Enum, Float, Int, Button, Any, Property
from traitsui.api import View, Item, Controller, UItem, HGroup, VGroup
from traitsui.editors import ListEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class ActionItem(HasTraits):
    attr = Enum('age', 'kca', 'rad40_percent', 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36', 'Ar41')
    comp = Enum('less than', 'greater than', 'between')
    value = Float
    value1 = Float
    start = Int(10)
    frequency = Int(5)

    label = Property(depends_on='attr,comp, value+, start, frequency')

    def assemble(self):
        c = self._get_label()

        return dict(attr=self.attr,
                    comp=self.label,
                    abbreviated_count_ratio=1.0,
                    frequency=self.frequency,
                    start=self.start)

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('attr'), UItem('comp'), UItem('value'),
                               UItem('value1', visible_when='comp=="between"')),
                        HGroup(Item('start'), Item('frequency')),
                        show_border=False))
        return v

    def _get_label(self):
        if self.comp == 'less than':
            c = '{}<{}'.format(self.attr, self.value)
        elif self.comp == 'greater than':
            c = '{}>{}'.format(self.attr, self.value)
        else:
            v = min(self.value, self.value1)
            v1 = max(self.value, self.value1)

            c = '{}<{}<{}'.format(v, self.attr, v1)
        return c


class ActionModel(HasTraits):
    actions = List
    add_button = Button
    remove_button = Button
    selected = Any

    def _add_button_fired(self):
        if self.selected:
            idx = self.actions.index(self.selected)
            obj = self.selected.clone_traits()
            self.actions.insert(idx, obj)
        else:
            obj = self.actions[-1].clone_traits()
            self.actions.append(obj)

    def _remove_button_fired(self):
        if len(self.actions) > 1:
            idx = -1
            if self.selected:
                idx = self.actions.index(self.selected)
            self.actions.pop(idx)

    def dump_yaml(self):
        return [d.assemble() for d in self.actions]

    def _actions_default(self):
        return [ActionItem(), ActionItem()]


class ActionEditor(Controller):
    def closed(self, info, is_ok):
        if is_ok:
            self.dump()

    def dump(self):
        p = self._get_path()
        if p:
            self._dump(p)

    def load(self):
        p = self._get_path()
        if p:
            self._load(p)

    def _load(self, p):
        pass

    def _dump(self, p):
        d = self.model.dump_yaml()
        with open(p, 'w') as fp:
            yaml.dump(d, fp, default_flow_style=False)

    def _get_path(self):
        p = '/Users/ross/Sandbox/actions.yaml'
        if not os.path.isfile(p):
            dlg = FileDialog(action='save as', default_directory='/Users/ross/Programming')
            if dlg.open():
                p = dlg.path

        return p

    def traits_view(self):
        v = View(

            HGroup(icon_button_editor('add_button', 'add'),
                   icon_button_editor('remove_button', 'delete')
            ),
            UItem('actions',
                  style='custom',
                  editor=ListEditor(
                      use_notebook=True,
                      selected='selected',
                      page_name='.label'
                      # style='custom',
                      #               mutable=False,
                      #               use_notebook=True,
                      #               selected='selected',
                      #               page_name='.attr',
                      #               view='traits_view',
                      #               editor=InstanceEditor()
                  )),
            buttons=['OK', 'Cancel'],
            resizable=True)
        return v
        # def traits_view(self):
        #     cols=[ObjectColumn(name='attr'),
        #           ObjectColumn(name='comp')
        #           ]
        #     v=View(UItem('actions', editor=TableEditor(columns=cols)), resizable=True)
        #     return v


if __name__ == '__main__':
    a = ActionEditor(model=ActionModel())
    a.configure_traits()

#============= EOF =============================================

