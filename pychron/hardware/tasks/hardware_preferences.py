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
from traits.api import Bool, List, on_trait_change, String, Dict
from traitsui.api import View, Item, Group, VGroup, HGroup, EnumEditor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from envisage.ui.tasks.preferences_pane import PreferencesPane
#============= standard library imports ========================
#============= local library imports  ==========================


class HardwarePreferences(BasePreferencesHelper):
    name = 'Hardware'
    preferences_path = 'pychron.hardware'
    enable_hardware_server = Bool

    auto_find_handle = Bool
    auto_write_handle = Bool

    system_lock_name = String
    system_lock_address = String
    enable_system_lock = Bool

    system_lock_names = List
    system_lock_addresses = Dict

    #    enable_directory_server = Bool
    #    directory_server_host = Str
    #    directory_server_port = Int
    #    directory_server_root = Str

    @on_trait_change('system_lock_name,enable_system_lock')
    def _update(self, obj, name, new):
        try:
            addr = self.system_lock_addresses[self.system_lock_name]
        except (TypeError, KeyError):
            return

        self.system_lock_address = addr


class HardwarePreferencesPane(PreferencesPane):
    model_factory = HardwarePreferences
    category = 'Hardware'

    def traits_view(self):
        v = View(
            VGroup(
                Group(
                    HGroup('enable_hardware_server', Item('enable_system_lock', enabled_when='enable_hardware_server')),
                    #                           Group(
                    #                                 Item('system_lock_name', editor=EnumEditor(values=self.system_lock_names),
                    #                                      enabled_when='enable_system_lock'),
                    #                                 Item('system_lock_address', style='readonly', label='Host'),
                    #                                      enabled_when='enable_hardware_server'),
                    label='Remote Hardware Server',
                    show_border=True
                ),
                #                     Group(
                #                           Item('enable_directory_server'),
                #                           Item('directory_server_root', enabled_when='enable_directory_server'),
                #                           Item('directory_server_host', enabled_when='enable_directory_server'),
                #                           Item('directory_server_port', enabled_when='enable_directory_server'),
                #                           show_border=True,
                #                           label='Directory Server'
                #                           ),
                Group(
                    'auto_find_handle',
                    Item('auto_write_handle', enabled_when='auto_find_handle'),
                    label='Serial',
                    show_border=True
                ),
            ),
            scrollable=True
        )
        return v

    #============= EOF =============================================
