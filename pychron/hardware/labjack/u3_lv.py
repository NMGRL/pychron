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
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.labjack.base_u3_lv import BaseU3LV


class U3LV(BaseU3LV, CoreDevice):
    pass

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
