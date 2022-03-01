# ===============================================================================
# Copyright 2014 Jake Ross
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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Float, Password, Bool, Enum
from traitsui.api import View, Item

from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.pychron_constants import SIMPLE, AR_AR


class SampleEntryPreferences(BasePreferencesHelper):
    preferences_path = "pychron.entry.sample"
    auto_add_project_repository = Bool


class SampleEntryPreferencesPane(PreferencesPane):
    model_factory = SampleEntryPreferences
    category = "Entry"

    def traits_view(self):
        v = View(
            Item(
                "auto_add_project_repository",
                label="Auto Add Project Repo.",
                tooltip="Automatically add a repository with the same name as the project",
            )
        )
        return v


class IrradiationEntryPreferences(BasePreferencesHelper):
    preferences_path = "pychron.entry"
    irradiation_prefix = Str
    monitor_name = Str
    monitor_material = Str
    j_multiplier = Float
    irradiation_project_prefix = Str
    allow_multiple_null_identifiers = Bool
    use_packet_for_default_identifier = Bool
    use_consecutive_identifiers = Bool
    mode = Enum(AR_AR, SIMPLE)


class LabnumberEntryPreferencesPane(PreferencesPane):
    model_factory = IrradiationEntryPreferences
    category = "Entry"

    def traits_view(self):
        irradiation_grp = BorderVGroup(
            Item(
                "irradiation_prefix",
                label="Irradiation Prefix",
                tooltip="Irradiation Prefix e.g., NM-",
            ),
            BorderHGroup(
                Item("monitor_name", label="Name"),
                Item("monitor_material", label="Material"),
                label="Monitor",
            ),
            Item("j_multiplier", label="J Multiplier", tooltip="J units per hour"),
            Item(
                "irradiation_project_prefix",
                tooltip="Project Prefix for Irradiations e.g., Irradiation-",
                label="Irradiation Project Prefix",
            ),
            Item(
                "allow_multiple_null_identifiers",
                label="Allow Multiple Null Identifiers",
                tooltip="If not selected a placeholder identifier "
                "is automatically generated. <IRRAD>:<LEVEL><POSITION>",
            ),
            Item(
                "use_packet_for_default_identifier",
                label="Use Packet for Default Identifier",
                tooltip="Use packet# when generating default "
                "identifiers instead of the hole#",
            ),
            Item(
                "use_consecutive_identifiers",
                tooltip="If unchecked partition monitors and unknowns when generated "
                "identifiers, otherwise identifiers are generated as "
                "a continuous sequence",
            ),
            label="Irradiations",
            visible_when='mode=="Ar/Ar"',
        )
        v = View(Item("mode"), irradiation_grp)
        return v


class SamplePrepPreferences(BasePreferencesHelper):
    preferences_path = "pychron.entry.sample_prep"
    host = Str
    username = Str
    password = Password
    root = Str


class SamplePrepPreferencesPane(PreferencesPane):
    model_factory = SamplePrepPreferences
    category = "Entry"

    def traits_view(self):
        imggrp = BorderVGroup(
            Item("host"),
            Item("username"),
            Item("password"),
            Item("root", label="Image folder"),
            label="Image Server",
        )
        v = View(imggrp)
        return v


# ============= EOF =============================================
