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
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, UItem, HGroup, VGroup, \
     EnumEditor, ButtonEditor, spring
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================

class GraphPane(TraitsTaskPane):
    id = 'bakeout.graph'
    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v

class ControllerPane(TraitsDockPane):
    id = 'bakeout.controller'
    name = 'Channels'
    def traits_view(self):
        controller_grp = HGroup()
        for tr in self.model._get_controller_names():
            controller_grp.content.append(UItem(tr, style='custom'))
        v = View(controller_grp)
        return v

class ControlsPane(TraitsDockPane):
    id = 'bakeout.controls'
    name = 'Controls'
    def traits_view(self):
        control_grp = VGroup(
                            HGroup(Item('execute',
                                        editor=ButtonEditor(label_value='execute_label'), show_label=False,
                                        enabled_when='execute_ok'),
                                   Item('training_run', label='Training Run')
                                   ),
                             VGroup(
                                    HGroup(Item('configuration',
                                         editor=EnumEditor(name='configurations'),
                                         show_label=False),
                                           Item('save',
                                         show_label=False)
                                    ),
                                    show_border=True,
                                    label='Configuration'
                                    ),
                             VGroup('include_pressure',
                                    'include_heat',
                                    'include_temp',
                                    label='Graphs',
                                    show_border=True,
                                    enabled_when='not active'),
                             VGroup(
                                    Item('update_interval',
                                         label='Sample Period (s)'),
                                    Item('scan_window', label='Data Window (mins)'),
                                    label='Scan',
                                    show_border=True,
                                    )
                             )
        v = View(control_grp)
        return v

#============= EOF =============================================
