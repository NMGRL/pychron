# ===============================================================================
# Copyright 2019 ross
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
from pychron.hardware.labjack.base_labjack import BaseLabjack
from traits.api import Enum, Str

from labjack import ljm


class BaseT4(BaseLabjack):

    connection_type = Enum('ANY', 'USB', 'TCP', 'ETHERNET',  'WIFI')
    identifier = Str

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:
            return self.load_additional_args(config)

    def open(self, *args, **kw):

        self._device = ljm.openS('T4', self.connection_type, self.identifier)
        # try:
        #     self._device = self._create_device()
        # except NullHandleException:
        #     return

        return True

    def load_additional_args(self, config):
        self.set_attribute(config, 'connection_type', 'Communications', 'connection_type')
        self.set_attribute(config, 'identifier', 'Communications', 'identifier')

        return True

    def initialize(self, *args, **kw):
        return True

    def set_channel_state(self, ch, state):
        """

        @param ch:
        @param state: bool True == channel on,  False == channel off
        @return:
        """
        ljm.eWriteName(self._device, ch, int(state))

    def get_channel_state(self, ch):
        result = ljm.eReadName(self._device, ch)
        return result

    def read_dac_channel(self, ch):
        pass

    # private
# ============= EOF =============================================
