# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, InstanceEditor, TableEditor, \
    ObjectColumn, HGroup, VGroup, Item, UReadonly

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


class CurrentDevicePane(TraitsTaskPane):
    id = 'hardware.current_device'

    def traits_view(self):
        v = View(
            UItem('selected',
                  style='custom',
                  editor=InstanceEditor(view='current_state_view')))
        return v


class ConfigurationPane(TraitsDockPane):
    id = 'hardware.configuration'
    name = 'Configuration'

    def trait_context(self):
        if self.model:
            return {'object': self.model.device_configurer,
                    'scan': self.model.device_configurer.scan_grp,
                    'pane': self}
        return super(TraitsDockPane, self).trait_context()

    def traits_view(self):
        comms_grp = VGroup(UItem('communication_grp',
                                 style='custom'),
                           visible_when='comms_visible',
                           show_border=True, label='Communications')

        scan_grp = VGroup(Item('scan.enabled'),
                          VGroup(Item('scan.graph'),
                                 Item('scan.record'),
                                 Item('scan.auto_start'),
                                 Item('scan.period'),
                                 enabled_when='scan.enabled'),
                          UItem('save_button'),
                          show_border=True, label='Scan')

        v = View(VGroup(HGroup(UReadonly('config_name'),
                               icon_button_editor('save_button', 'document-save',
                                                  enabled_when='config_path')),
                        comms_grp,
                        scan_grp),
                 height=500,
                 resizable=True)
        return v


class InfoPane(TraitsDockPane):
    id = 'hardware.info'
    name = 'Current Device'

    def traits_view(self):
        v = View(UItem('selected',
                       style='custom',
                       editor=InstanceEditor(view='info_view')))
        return v


class DevicesPane(TraitsDockPane):
    id = 'hardware.devices'
    name = 'Devices'

    def traits_view(self):
        cols = [ObjectColumn(name='name'),
                ObjectColumn(name='connected'),
                ObjectColumn(name='com_class', label='Com. Class'),
                ObjectColumn(name='klass', label='Class')]
        table_editor = TableEditor(columns=cols,
                                   editable=False,
                                   selected='selected',
                                   selection_mode='row')
        v = View(UItem('devices', editor=table_editor))
        return v

# ============= EOF =============================================
