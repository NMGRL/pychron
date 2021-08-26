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
try:
    import u3
    from LabJackPython import NullHandleException
except ImportError:
    NullHandleException = BaseException

import re
# ============= local library imports  ==========================

DIORE = re.compile(r'^[FCE]IO\d+$')


class BaseU3LV:
    _device = None
    _dio_mapping = None
    _dio_channels = None

    def load(self, *args, **kw):
        self._dio_mapping = {}
        config = self.get_configuration()
        if config:
            section = 'Communications'
            conn = {'autoOpen': False}
            if config.has_section(section):
                conn['localId'] = config.get(section, 'localId', fallback=None)
                conn['serial'] = config.get(section, 'serialNum', fallback=None)
                conn['firstFound'] = False
            self.debug('connection={}'.format(conn))
            try:
                self._device = u3.U3(**conn)
            except NullHandleException:

                self.debug_exception()
                return
            return self.load_additional_args(config)

    def open(self, *args, **kw):
        try:
            self._device.open()
            return True
        except BaseException as e:
            self.debug_exception()

    def load_additional_args(self, config):
        mapping = {}
        section = 'DIOMapping'
        if config.has_section(section):
            for option in config.options(section):
                u3channel = config.get(section, option)
                mapping[option] = getattr(u3, u3channel)
            self._dio_mapping = mapping

        elif config.has_section('DIOConfig'):
            channellist = config.get('DIOConfig', 'channellist')
            self._dio_channels = [getattr(u3, c.strip()) for c in channellist.split(',')]

        return True

    def initialize(self, *args, **kw):
        chs = None
        if self._dio_mapping:
            chs = [v for v in self._dio_mapping.values()]
        elif self._dio_channels:
            chs = self._dio_channels

        if chs:
            chs = [v for v in chs if v not in (u3.CIO0, u3.CIO1, u3.CIO2, u3.CIO3)]
            print('configuring {}'.format(chs))
            self._device.configDigital(*chs)

        return True

    def set_channel_state(self, ch, state):
        """

        @param ch:
        @param state: bool True == channel on,  False == channel off
        @return:
        """
        pin = self._get_pin(ch)
        print('set channel state {} {} state={}'.format(ch, pin, state))
        if pin is not None:
            self._device.setDOState(pin, int(not state))
            return True

    def get_channel_state(self, ch):
        pin = self._get_pin(ch)
        print('get chanel state {} {}'.format(ch, pin))
        if pin is not None:
            r = self._device.getDIOState(pin)
            print('got channel state {} {}'.format(r, not r))
            return not r

    # def read_dac_channel(self, ch):
    #     v = self._device.getFIOState(ch)
    #     return v

    def read_temperature(self):
        v = self._device.getTemperature()
        return v

    def close(self):
        self._device.reset(True)
        self._device.close()

    def read_adc_channel(self, ch):
        if not isinstance(ch, int):
            ch = self._get_pin(ch)
        return self._device.getAIN(ch)

    def set_dac_channel(self, dac_id, v):
        bits = self._device.voltageToDACBits(v, dacNumber=dac_id, is16Bits=False)
        self.debug('setting voltage={}, {}'.format(v, bits))
        self._device.getFeedback(u3.DAC0_8(bits))

    # private
    def _get_pin(self, ch):
        ch = str(ch)
        if DIORE.match(ch):
            return getattr(u3, ch)
        else:
            try:
                return self._dio_mapping[ch]
            except KeyError:
                self.warning('Invalid channel {}'.format(ch))
                self.warning('DIOMapping {}'.format(self._dio_mapping))

# ============= EOF =============================================
