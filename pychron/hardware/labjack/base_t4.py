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
from traits.api import Enum, Str, HasTraits
from pychron.hardware.core.data_helper import make_bitarray

from labjack import ljm


class BaseT4(BaseLabjack, HasTraits):
    connection_type = Enum("ANY", "USB", "TCP", "ETHERNET", "WIFI")
    identifier = Str
    dio = Str

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:
            return self.load_additional_args(config)

    def open(self, *args, **kw):
        self._device = ljm.openS("T4", self.connection_type, self.identifier)
        return True

    def load_additional_args(self, config):

        ct = self.config_get(config, "Communications", "type")
        if ct:
            try:
                self.connection_type = ct.upper()
            except TraitError:
                self.warning("Invalid connection type. {}".format(ct))

        self.set_attribute(config, "identifier", "Communications", "identifier")
        self.set_attribute(config, "dio", "General", "dio")

        return True

    def initialize(self, *args, **kw):
        if self.dio:
            for dio in self.dio.split(","):
                # read from the dio
                self.get_channel_state(dio)

        return True

    def set_channel_state(self, ch, state):
        """

        @param ch:
        @param state: bool True == channel on,  False == channel off
        @return:
        """
        ljm.eWriteName(self._device, ch, int(state))

    def get_channel_state(self, ch):
        ret = None
        if ch.lower().startswith("eio"):
            ret = self._get_eio_state(ch)

        return ret

    def read_dac_channel(self, ch):
        pass

    # private
    def _get_eio_state(self, ch):
        v = ljm.eReadName(self._device, "EIO_STATE")
        ba = make_bitarray(int(v))
        self.debug("eio state={} ba={}, ch={}".format(int(v), ba, ch))

        idx = 7 - int(ch[3:])
        return bool(int(ba[idx]))


# ============= EOF =============================================
