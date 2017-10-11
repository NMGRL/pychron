# ===============================================================================
# Copyright 2016 Jake Ross
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
# ============= standard library imports ========================
import u3
from LabJackPython import NullHandleException
# ============= local library imports  ==========================


class BaseU3LV:
    _device = None
    _dio_mapping = None

    def load(self, *args, **kw):
        self._dio_mapping = {}

        try:
            self._device = u3.U3()
        except NullHandleException:
            return

        config = self.get_configuration()
        if config:
            return self.load_additional_args(config)

    def open(self, *args, **kw):
        return True

    def load_additional_args(self, config):
        mapping = {}
        section = 'DIOMapping'
        if config.has_section(section):
            for option in config.options(section):
                u3channel = config.get(section, option)
                mapping[option] = getattr(u3, u3channel)
        self._dio_mapping = mapping

        return True

    def initialize(self, *args, **kw):

        chs = [v for v in self._dio_mapping.itervalues() if v not in (u3.CIO0, u3.CIO1, u3.CIO2, u3.CIO3)]
        self._device.configDigital(*chs)

        return True

    def set_channel_state(self, ch, state):
        """

        @param ch:
        @param state: bool True == channel on,  False == channel off
        @return:
        """
        pin = self._get_pin(ch)
        print 'sdafasfdasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf', ch, pin, state
        if pin is not None:
            self._device.setDOState(pin, int(not state))

    def get_channel_state(self, ch):
        pin = self._get_pin(ch)
        if pin is not None:
            return self._device.getDIOState(pin)

    def read_dac_channel(self, ch):
        v = self._device.getFIOState(ch)
        return v

    def read_temperature(self):
        v = self._device.getTemperature()
        return v

    def close(self):
        self._device.reset(True)
        self._device.close()

    # private
    def _get_pin(self, ch):
        try:
            return self._dio_mapping[str(ch)]
        except KeyError:
            self.warning('Invalid channel {}'.format(ch))
            self.warning('DIOMapping {}'.format(self._dio_mapping))

# ============= EOF =============================================



