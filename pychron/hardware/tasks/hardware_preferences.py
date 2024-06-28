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
from __future__ import absolute_import
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Bool, List, on_trait_change, String, Dict, Str, Int, HasTraits
from traitsui.api import View, Item, VGroup, UItem, TableEditor
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
    name = "Hardware"
    preferences_path = "pychron.hardware"
    enable_hardware_server = Bool

    auto_find_handle = Bool
    auto_write_handle = Bool

    system_lock_name = String
    system_lock_address = String
    enable_system_lock = Bool

    system_lock_names = List
    system_lock_addresses = Dict

    # use_twisted = Bool(True)
    pnames = List
    ports = Dict
    factories = Dict
    _protocols = List

    def _initialize(self, *args, **kw):
        super(HardwarePreferences, self)._initialize(*args, **kw)
        ap = (
            ("ValveProtocol", "pychron.tx.factories.ValveFactory"),
            ("FusionsCO2Protocol", "pychron.tx.factories.FusionsCO2Factory"),
            ("FusionsDiodeProtocol", "pychron.tx.factories.FusionsDiodeFactory"),
            ("OsTechDiodeProtocol", "pychron.tx.factories.OsTechDiodeFactory"),
            ("FusionsUVProtocol", "pychron.tx.factories.FusionsUVFactory"),
            ("FurnaceProtocol", "pychron.tx.factories.FurnaceFactory"),
            ("AquAProtocol", "pychron.tx.factories.AquAFactory"),
        )
        self._protocols = [
            Protocol(
                name=n,
                factory=f,
                port=self.ports.get(n, 8000),
                enabled=n in self.pnames,
            )
            for n, f in ap
        ]

    @on_trait_change("_protocols:[port,enabled]")
    def _handle_protocol(self, new):
        ps = (p for p in self._protocols if p.enabled)

        self.pnames = [p.name for p in ps]
        self.ports = {p.name: p.port for p in self._protocols}
        self.factories = {p.name: p.factory for p in self._protocols}

    @on_trait_change("system_lock_name,enable_system_lock")
    def _update(self, obj, name, new):
        try:
            addr = self.system_lock_addresses[self.system_lock_name]
        except (TypeError, KeyError):
            return

        self.system_lock_address = addr


class HardwarePreferencesPane(PreferencesPane):
    model_factory = HardwarePreferences
    category = "Hardware"

    def traits_view(self):
        cols = [
            CheckboxColumn(name="enabled"),
            ObjectColumn(name="name", editable=False),
            ObjectColumn(name="port"),
        ]

        txgrp = VGroup(
            UItem("_protocols", editor=TableEditor(columns=cols)),
            enabled_when="enable_hardware_server",
        )

        ehs_grp = VGroup(
            Item("enable_hardware_server", label="Enabled"),
            txgrp,
            # VGroup(Item('use_twisted'),
            #        txgrp,
            #        # Item('enable_system_lock'),
            #        enabled_when='enable_hardware_server'),
            show_border=True,
            label="Pychron Proxy Server",
        )

        # sgrp = VGroup(Item('auto_find_handle'),
        #               Item('auto_write_handle', enabled_when='auto_find_handle'),
        #               show_border=True, label='Serial')
        # v = View(VGroup(ehs_grp, sgrp))
        v = View(ehs_grp)
        return v


# ============= EOF =============================================
