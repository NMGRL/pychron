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
from traits.api import Bool, Int
from traitsui.api import Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.extraction_line.tasks.extraction_line_preferences import ExtractionLinePreferencesPane, \
    BaseExtractionLinePreferences


class ClientExtractionLinePreferences(BaseExtractionLinePreferences):
    name = 'ClientExtractionLine'

    use_status_monitor = Bool
    valve_state_frequency = Int(3)
    valve_lock_frequency = Int(5)
    valve_owner_frequency = Int(5)
    update_period = Int(1)
    checksum_frequency = Int(3)


class ClientExtractionLinePreferencesPane(ExtractionLinePreferencesPane):
    model_factory = ClientExtractionLinePreferences
    category = 'ExtractionLine'

    def _get_status_group(self):
        s_grp = VGroup(Item('use_status_monitor'),
                       VGroup(Item('update_period', tooltip='Delay between iterations in seconds'),
                              VGroup(
                                  Item('valve_state_frequency', label='State',
                                       tooltip='Check Valve State, i.e Open or Closed every N iterations'),
                                  Item('checksum_frequency', label='Checksum',
                                       tooltip='Check the entire extraction line state every N iterations'),
                                  Item('valve_lock_frequency', label='Lock',
                                       tooltip='Check Valve Software Lock. i.e Locked or unlocked every N iterations'),
                                  Item('valve_owner_frequency', label='Owner',
                                       tooltip='Check Valve Owner every N iterations'),
                                  label='Frequencies'),
                              enabled_when='use_status_monitor'),
                       label='Status Monitor')

        return s_grp

    def _get_valve_group(self):
        v_grp = VGroup(self._network_group(),
                       show_border=True,
                       label='Valves')

        return v_grp

    def _get_tabs(self):
        return super(ClientExtractionLinePreferencesPane, self)._get_tabs() + (self._get_status_group(),)

# ============= EOF =============================================
