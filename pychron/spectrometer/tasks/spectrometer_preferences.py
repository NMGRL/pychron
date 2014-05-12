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
from traits.api import Bool
from traitsui.api import View, Item, VGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper





#============= standard library imports ========================
#============= local library imports  ==========================


class SpectrometerPreferences(BasePreferencesHelper):
    name = 'Spectrometer'
    preferences_path = 'pychron.spectrometer'
    id = 'pychron.spectrometer.preferences_page'
    send_config_on_startup = Bool
    use_local_mftable_archive = Bool
    use_db_mftable_archive = Bool


class SpectrometerPreferencesPane(PreferencesPane):
    model_factory = SpectrometerPreferences
    category = 'Spectrometer'

    def traits_view(self):
        return View(VGroup(
            Item('send_config_on_startup',
                 tooltip='Load the spectrometer parameters on startup'),
            VGroup(Item('use_local_mftable_archive',
                        tooltip='Archive mftable to a local git repository',
                        label='Local Archive'),
                   Item('use_db_mftable_archive',
                        tooltip='Archive mftable to central database',
                        label='DB Archive'),
                   label='MFTable')))

#============= EOF =============================================
