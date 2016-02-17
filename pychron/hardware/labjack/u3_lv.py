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
import time
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice
import u3


class U3LV(CoreDevice):
    def load(self, *args, **kw):
        self._device = u3.U3()
        return True

    def open(self, *args, **kw):
        return True

    def initialize(self, *args, **kw):
        eio = [0, 1, 2, 3, 4, 5, 6, 7]
        fio = []

        args = [getattr(u3, '{}IO{}'.format(k, i))
                for k, pins in (('F', fio), ('E', eio))
                for i in pins]

        self._device.configDigital(*args)

        self.channel_mapping = {'1': u3.CIO0,
                                '2': u3.CIO1,
                                '3': u3.CIO2,
                                '4': u3.CIO3,
                                '5': u3.EIO1,
                                '6': u3.EIO0,
                                '7': u3.EIO3,
                                '8': u3.EIO2,
                                '9': u3.EIO5,
                                '10': u3.EIO4,
                                '11': u3.EIO7,
                                '12': u3.EIO6,
                                '13': u3.FIO2,
                                '14': u3.FIO0,
                                '15': u3.FIO3,
                                '16': u3.FIO1,
                                }
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
            return self.channel_mapping[str(ch)]
        except KeyError:
            self.warning('Invalid channel {}'.format(ch))


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import paths

    paths.build('_dev')

    logging_setup('adc', use_archiver=False)

    # paths.build('_dev')

    a = U3LV(name='U3LV')
    a.bootstrap()
    # print a.read_dac_channel(1)
    # print a.read_temperature()
    #
    # for i in range(10):
    #     a.set_channel_state(0, i % 3)
    #     time.sleep(1)

    for i in range(1,17):
        a.set_channel_state(str(i), 1)
        time.sleep(0.5)
        a.set_channel_state(str(i), 0)
        time.sleep(0.5)

    # while 1:
    #     cmd = raw_input('set pin to ... >> ')
    #     if cmd in ('e', 'exit', 'q', 'quit'):
    #         break
    #
    #     ch, state = map(str.strip, cmd.split(' '))
    #     a.set_channel_state(ch, int(state))

    a.close()
    # a = MultiBankADCExpansion(name='proxr_adc')
    # a.bootstrap()
    # a.load_communicator('serial', port='usbserial-A5018URQ', baudrate=115200)
    # a.open()

# ============= EOF =============================================
