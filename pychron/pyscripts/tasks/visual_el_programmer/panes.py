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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, Item, HGroup, VGroup, UItem, Group
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from enable.component_editor import ComponentEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.code_editor import PyScriptCodeEditor


class CentralPane(TraitsTaskPane):
    def traits_view(self):
        canvas_group = HGroup(
            UItem('canvas', style='custom',
                  editor=ComponentEditor()),
            label='Canvas')

        script_group = VGroup(UItem('script_text',
                                    editor=PyScriptCodeEditor(),
                                    style='custom'),
                              label='script')

        tgrp = Group(canvas_group, script_group, layout='tabbed')
        v = View(tgrp)
        return v


class ActionsAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value')]

    def get_bg_color(self, *args, **kw):
        color = 'white'
        if self.item.name == 'open':
            color = 'lightgreen'
        elif self.item.name == 'close':
            color = 'lightcoral'
        return color


class ControlPane(TraitsDockPane):
    id = 'pychron.pyscript.visual.control'
    name = 'Controls'
    closable = False

    def traits_view(self):
        action_grp = VGroup(HGroup(UItem('add_sleep_button', width=-40),
                                   UItem('duration')),
                            HGroup(UItem('add_info_button', width=-40),
                                   UItem('info_str')),
                            HGroup(Item('record_valve_actions', label='Record Actions')),
                            UItem('actions', editor=TabularEditor(adapter=ActionsAdapter(),
                                                                  operations=['move', 'delete'],
                                                                  selected='selected',
                                                                  refresh='refresh_needed',
                                                                  multi_select=True)))
        v = View(action_grp)
        return v

#============= EOF =============================================

