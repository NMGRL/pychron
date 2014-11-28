# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
from traitsui.api import View, UItem, InstanceEditor, TableEditor, ObjectColumn
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================

class CurrentDevicePane(TraitsTaskPane):
    id = 'hardware.current_device'

    def traits_view(self):
        v = View(
                 UItem('current_device',
#                 UItem('selected',
                          style='custom',
                          editor=InstanceEditor(view='current_state_view')
                          )
               )
        return v

class InfoPane(TraitsDockPane):
    id = 'hardware.info'
    name = 'Current Device'
    def traits_view(self):
        v = View(UItem('current_device',
                          style='custom',
                          editor=InstanceEditor(view='info_view')
                          )
               )
        return v

class DevicesPane(TraitsDockPane):
    id = 'hardware.devices'
    name = 'Devices'
    def traits_view(self):
        cols = [ObjectColumn(name='name'),
                ObjectColumn(name='connected'),
                ObjectColumn(name='com_class', label='Com. Class'),
                ObjectColumn(name='klass', label='Class'),

                ]
        table_editor = TableEditor(columns=cols,
                                   editable=False,
                                   selected='selected',
                                   selection_mode='row'

                                   )
        v = View(UItem('devices', editor=table_editor),
                 )
        return v
# ============= EOF =============================================
