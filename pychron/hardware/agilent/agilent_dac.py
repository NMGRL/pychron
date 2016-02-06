# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Float, Str, Int

# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class AgilentDAC(CoreDevice):
    id_query = ''
    value = Float(0)
    slot_number = Str('1')

    dac_bits = Int

    min_value = Float(0)
    max_value = Float(100)

    def initialize(self):
        self.communicator.terminator = chr(10)
        return True

    # ===========================================================================
    # configloadable interface
    # ===========================================================================
    def load_additional_args(self, config):

        self.min_value = self.config_get(config, 'General', 'min', cast='float', default=0.0, optional=True)
        self.max_value = self.config_get(config, 'General', 'max', cast='float', default=100.0, optional=True)
        self.slot_number = self.config_get(config, 'General', 'slot', default='1', optional=True)
        self.channel_number = '{:02d}'.format(self.config_get(config, 'General', 'channel', cast='int', default='4', optional=True))

        if self.channel_number not in ['04', '05']:
            self.warning('Invalid channel number {} setting to default: 04'.format(self.channel_number))
            return False

        self.dac_bits = 2 ** self.config_get(config, 'General', 'bits', cast='int', optional=True, default=10)

        return True
    # ===============================================================================
    # icore device interface
    # ===============================================================================

    def set(self, v):
        self.set_dac_value(v)

    def get(self, *args, **kw):
        return super(AgilentDAC, self).get(*args, **kw) or self.value
        # v = CoreDevice.get(self)
        # if v is None:
        #     v = self.value
        # return v

    # ===============================================================================
    # AgilentDAC interface
    # ===============================================================================
    def set_dac_value(self, value):
        self.value = value
        # convert real world value to dac value
#        value = value / self.max_value * self.dac_bits

        cmd = 'SOURCE:VOLTAGE {:n} (@{}{})'.format(value, self.slot_number, self.channel_number)
        resp = self.ask(self._build_command(cmd))
        return self._parse_response(resp)

    def read_dac_value(self,):
        cmd = 'SF'
        resp = self.ask(self._build_command(cmd))
        return self._parse_response(resp)

    # ===============================================================================
    # private interface
    # ===============================================================================
    def _build_command(self, cmd, *args, **kw):
        return cmd

    def _parse_response(self, resp, *args, **kw):
        return resp
# ============= EOF =====================================
