# ===============================================================================
# Copyright 2016 Jake Ross
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
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Instance, DelegatesTo, \
    Button, String
from traitsui.api import View, UItem, HGroup, VGroup, Controller, Action, TabularEditor, EnumEditor
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
import re

# ============= local library imports  ==========================

from pychron.loading.loading_manager import LoadPosition

POSITION_RANGE_REGEX = re.compile(r'^\d+(-\d+)*(,\d+(-\d+)*)*$')


class SelectionStr(String):
    def validate(self, obj, name, value):
        if not value or POSITION_RANGE_REGEX.match(value):
            return value
        else:
            self.error(obj, name, value)


class LoadViewSelectionModel(HasTraits):
    is_append = False
    manager = Instance('pychron.loading.loading_manager.LoadingManager')

    positions = DelegatesTo('manager')
    selected_positions = DelegatesTo('manager')
    canvas = DelegatesTo('manager')
    load_name = DelegatesTo('manager')
    loads = DelegatesTo('manager')

    selection_str = SelectionStr(enter_set=True, auto_set=False)
    select_all_button = Button('Select All')

    def _selection_str_changed(self, new):
        if new:
            fs = [(ps.labnumber, pp) for ps in self.positions
                  for pp in ps.positions]

            def func(idx):
                pp = next((p for p in fs if p[1] == idx))
                return LoadPosition(labnumber=pp[0], positions=[idx])

            ss = []
            for r in new.split(','):
                if '-' in r:
                    s, e = map(int, r.split('-'))
                    e += 1
                else:
                    s = int(r)
                    e = s + 1

                ss.extend([func(i) for i in xrange(s, e)])

            self.selected_positions = ss

    def _select_all_button_fired(self):
        self.selected_positions = [LoadPosition(labnumber=ps.labnumber,
                                                positions=[pp]) for ps in self.positions
                                   for pp in ps.positions]


class PositionsAdapter(TabularAdapter):
    columns = [('Identifier', 'labnumber'),
               ('Position', 'position_str')]


class AppendAction(Action):
    name = 'Append'
    action = 'append'


class ReplaceAction(Action):
    name = 'Replace'
    action = 'replace'


class LoadViewSelectionController(Controller):
    model = LoadViewSelectionModel

    def append(self, info):
        self.model.is_append = True
        info.ui.dispose()

    def replace(self, info):
        self.model.is_append = False
        info.ui.dispose()

    def traits_view(self):
        grp = VGroup(UItem('load_name', editor=EnumEditor(name='loads')),
                     HGroup(UItem('selection_str'), UItem('select_all_button')),
                     HGroup(UItem('canvas',
                                  editor=ComponentEditor(),
                                  style='custom'),
                            UItem('selected_positions', editor=TabularEditor(adapter=PositionsAdapter()))))
        v = View(grp, title='Load Selection',
                 kind='livemodal',
                 resizable=True,
                 buttons=[AppendAction(), ReplaceAction(), 'Cancel'])
        return v

# ============= EOF =============================================
