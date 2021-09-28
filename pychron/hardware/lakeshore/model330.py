# ===============================================================================
# Copyright 2018 ross
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

from traitsui.api import Item, UItem, HGroup, VGroup, Spring

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController
from pychron.hardware import get_float
import time


class Model330TemperatureController(BaseLakeShoreController):

    # def set_setpoint(self, v, output=1, retries=3):
    #
    #     self.set_range(v)
    #     for i in range(retries):
    #         self.tell('SETP {}'.format(v))
    #         time.sleep(2)
    #         sp = self.read_setpoint(output, verbose=True)
    #         self.debug('setpoint set to={} target={}'.format(sp, v))
    #         if sp == v:
    #             break
    #         time.sleep(1)
    #
    #     else:
    #         self.warning_dialog('Failed setting setpoint to {}. Got={}'.format(v, sp))

    def set_range(self, v):
        # if v <= 10:
        #     self.tell('RANGE {},{}'.format(output, 1))
        # elif 10 < v <= 30:
        #     self.tell('RANGE {},{}'.format(output, 2))
        # else:
        #     self.tell('RANGE {},{}'.format(output, 3))

        for r in self.range_tests:
            ra = r.test(v)
            if ra:
                self.tell('RANG {}'.format(ra))
                break

        time.sleep(1)

    @get_float(default=0)
    def read_setpoint(self, output, verbose=False):
        if output is not None:
            return self.ask('SETP?', verbose=verbose)

    def get_control_group(self):
        grp = VGroup(Spring(height=10, springy=False),
                     HGroup(Item('input_a', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Item('setpoint1'),
                            UItem('setpoint1_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)),
                     HGroup(Item('input_b', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                            Spring(width=10, springy=False)))
        return grp

# ============= EOF =============================================
