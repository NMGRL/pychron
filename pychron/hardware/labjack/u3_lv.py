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
import time
import u3
# ============= local library imports  ==========================
from LabJackPython import NullHandleException

from pychron.hardware.core.core_device import CoreDevice


class U3LV(CoreDevice):
    _device = None
    _dio_mapping = None

    def load(self, *args, **kw):
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


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import paths

    paths.build('_dev')

    logging_setup('adc', use_archiver=False)

    # paths.build('_dev')

    a = U3LV(name='u3lv', configuration_dir_name='furnace')
    a.bootstrap()
    # print a.read_dac_channel(1)
    # print a.read_temperature()
    #
    # for i in range(10):
    #     a.set_channel_state(0, i % 3)
    #     time.sleep(1)

    # for i in range(1, 17):
    #     a.set_channel_state(str(i), 1)
    #     time.sleep(0.5)
    #     a.set_channel_state(str(i), 0)
    #     time.sleep(0.5)

    # while 1:
    #     cmd = raw_input('set pin to ... >> ')
    #     if cmd in ('e', 'exit', 'q', 'quit'):
    #         break
    #
    #     ch, state = map(str.strip, cmd.split(' '))
    #     a.set_channel_state(ch, int(state))

    for i in range(30):
        print i, a.get_channel_state('13')
        time.sleep(1)
    a.close()

# ============= EOF =============================================
