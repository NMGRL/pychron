# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Str
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.abstract_device import AbstractDevice
from pychron.hardware.core.core_device import CoreDevice


class NMGRLMagnetDumper(CoreDevice):
    _dump_in_progress = False

    def energize(self):
        self._dump_in_progress = True
        self.ask('EnergizeMagnets')

    def denergize(self):
        self._dump_in_progress = False
        self.ask('DenergizeMagnets')

    def is_energized(self):
        ret = self.ask('IsEnergized', verbose=True) == 'OK'
        self._dump_in_progress = ret
        return ret

    # channel_address = Str
    # in_progress_address = Str
    # _dump_in_progress = False
    #
    # def load_additional_args(self, config):
    #     self.set_attribute(config, 'channel_address', 'General', 'channel_address')
    #     self.set_attribute(config, 'in_progress_address', 'General', 'in_progress_address')
    #     super(NMGRLMagnetDumper, self).load_additional_args(config)
    #
    # def actuate(self):
    #     if self._cdevice:
    #         self._dump_in_progress = True
    #         self._cdevice.open_channel(self.channel_address)
    #
    def dump_in_progress(self):
        state = False
        if self._dump_in_progress:
            state = self.ask('GetMagnetsState')
            if not state:
                self._dump_in_progress = False
        return state

# ============= EOF =============================================
