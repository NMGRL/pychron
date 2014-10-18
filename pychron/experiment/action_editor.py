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

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui import set_qt
from pychron.paths import paths


set_qt()


#============= enthought library imports =======================
import os
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, List, Enum, Float, Int, Button, Any, Property, Str
from traitsui.api import View, Item, Controller, UItem, HGroup, VGroup
from traitsui.editors import ListEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class ActionItem(HasTraits):
    attr = Enum('age', 'kca', 'rad40_percent', 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36', 'Ar41', '37/39')
    comp = Enum('less than', 'greater than', 'between')
    value = Float
    value1 = Float
    start = Int(10)
    frequency = Int(5)

    label = Property(depends_on='attr,comp, value+, start, frequency')

    def __init__(self, saved_state=None, *args, **kw):
        super(ActionItem, self).__init__(*args, **kw)

        if saved_state:
            saved_state.pop('comp')
            self.trait_set(**saved_state)

    def assemble(self):
        return dict(attr=self.attr,
                    check=self.label,
                    value=self.value,
                    value1=self.value,
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
    path = Str

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

    def load_yaml(self, yd):
        self.actions = [ActionItem(saved_state=yi) for yi in yd]

    def dump_yaml(self):
        yd = [d.assemble() for d in self.actions]
        return yd

    def _actions_default(self):
        return [ActionItem()]


class ActionEditor(Controller):
    # def init( self, info):
    #     self.load()
    # @on_trait_change('model:path')
    # def _handle_path(self):
    #     if self.model.path:
    #
    #         self.info.title=os.path.basename(self.model.path)
    title = Str

    def init(self, info):
        # print 'fdas', self.title
        # if self.model.path:  #
        if self.title:
            info.ui.title = self.title

    def closed(self, info, is_ok):
        if is_ok:
            self.dump()

    def dump(self):
        p = self._get_path()
        if p:
            self._dump(p)

    def load(self, p):
        if p:
            self.title = os.path.basename(p)
            self._load(p)

    def _load(self, p):
        if not self.model:
            self.model = ActionModel()

        self.model.path = p
        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            self.model.load_yaml(yd)

    def _dump(self, p):
        d = self.model.dump_yaml()
        with open(p, 'w') as fp:
            yaml.dump(d, fp, default_flow_style=False)
            self.model.path = p

    def _get_path(self):
        p = self.model.path
        if not p:
            p = '/Users/ross/Sandbox/actions.yafml'

        if not os.path.isfile(p):
            p = None
            dlg = FileDialog(action='save as', default_directory=paths.conditionals_dir)
            if dlg.open():
                p = dlg.path.strip()
                if p:
                    p = add_extension(p, '.yaml')

        return p

    def traits_view(self):
        v = View(

            HGroup(icon_button_editor('add_button', 'add'),
                   icon_button_editor('remove_button', 'delete')),
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

