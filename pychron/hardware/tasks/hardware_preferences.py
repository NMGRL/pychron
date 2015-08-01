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

# ============= enthought library imports =======================
from traits.api import Bool, List, on_trait_change, String, Dict, Str, Int, HasTraits
from traitsui.api import View, Item, VGroup, UItem, TableEditor
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


# ============= standard library imports ========================
# ============= local library imports  ==========================
class Protocol(HasTraits):
    name = Str
    enabled = Bool
    port = Int


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

    use_twisted = Bool

    _protocols = List

    pnames = List
    ports = Dict
    factories = Dict

    def _initialize(self, *args, **kw):
        super(HardwarePreferences, self)._initialize(*args, **kw)
        ap = (('ValveProtocol', 'pychron.tx.factories.ValveFactory'),)
        self._protocols = [Protocol(name=n, factory=f,
                                    port=self.ports.get(n, 8000),
                                    enabled=n in self.pnames) for n, f in ap]

    @on_trait_change('_protocols:[port,enabled]')
    def _handle_protocol(self, new):
        self.pnames = [p.name for p in self._protocols]
        self.ports = {p.name: p.port for p in self._protocols}
        self.factories = {p.name: p.factory for p in self._protocols}

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
        cols = [CheckboxColumn(name='enabled'),
                ObjectColumn(name='name', editable=False),
                ObjectColumn(name='port')]

        txgrp = VGroup(UItem('_protocols',
                             editor=TableEditor(columns=cols)))
        ehs_grp = VGroup(Item('enable_hardware_server', label='Enabled'),
                         VGroup(Item('use_twisted'),
                                txgrp,
                                Item('enable_system_lock'),
                                enabled_when='enable_hardware_server'),
                         show_border=True, label='Pychron Proxy Server')

        sgrp = VGroup(Item('auto_find_handle'),
                      Item('auto_write_handle', enabled_when='auto_find_handle'),
                      show_border=True, label='Serial')
        v = View(VGroup(ehs_grp, sgrp))
        return v

        # ============= EOF =============================================
        # v = View(
        #     VGroup(
        #         Group(
        #             HGroup(Item('enable_hardware_server'),
        #                    Item('enable_system_lock', enabled_when='enable_hardware_server')),
        #             #                           Group(
        #             #                             Item('system_lock_name', editor=EnumEditor(values=self.system_lock_names),
        #             #                                      enabled_when='enable_system_lock'),
        #             #                                 Item('system_lock_address', style='readonly', label='Host'),
        #             #                                      enabled_when='enable_hardware_server'),
        #             label='Remote Hardware Server',
        #             show_border=True
        #         ),
        #         #                     Group(
        #         #                           Item('enable_directory_server'),
        #         #                           Item('directory_server_root', enabled_when='enable_directory_server'),
        #         #                           Item('directory_server_host', enabled_when='enable_directory_server'),
        #         #                           Item('directory_server_port', enabled_when='enable_directory_server'),
        #         #                           show_border=True,
        #         #                           label='Directory Server'
        #         #                           ),
        #         Group(
        #             'auto_find_handle',
        #             Item('auto_write_handle', enabled_when='auto_find_handle'),
        #             label='Serial',
        #             show_border=True
        #         ),
        #     ),
        #     scrollable=True
        # )
        # return v
