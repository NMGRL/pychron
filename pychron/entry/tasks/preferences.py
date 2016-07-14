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
from traits.api import Str, Float, Password
from traitsui.api import View, Item, Group, VGroup, HGroup, UItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class IrradiationEntryPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.entry'
    irradiation_prefix = Str
    monitor_name = Str
    monitor_material = Str
    j_multiplier = Float


class LabnumberEntryPreferencesPane(PreferencesPane):
    model_factory = IrradiationEntryPreferences
    category = 'Entry'

    def traits_view(self):
        irradiation_grp = Group(Item('irradiation_prefix',
                                     label='Irradiation Prefix'),
                                HGroup(UItem('monitor_name'),
                                       UItem('monitor_name'),
                                       show_border=True, label='Monitor'),
                                Item('j_multiplier', label='J Multiplier',
                                     tooltip='J units per hour'),
                                show_border=True,
                                label='Irradiations')
        v = View(irradiation_grp)
        return v


class SamplePrepPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.entry.sample_prep'
    host = Str
    username = Str
    password = Password
    root = Str


class SamplePrepPreferencesPane(PreferencesPane):
    model_factory = SamplePrepPreferences
    category = 'Entry'

    def traits_view(self):
        imggrp = VGroup(Item('host'),
                        Item('username'),
                        Item('password'),
                        Item('root', label='Image folder'),
                        show_border=True,
                        label='Image Server')
        v = View(imggrp)
        return v

# ============= EOF =============================================
