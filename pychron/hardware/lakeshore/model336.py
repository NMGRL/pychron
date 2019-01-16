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
from __future__ import absolute_import
from traitsui.api import Group, Item, UItem, HGroup, VGroup, spring, Spring, Label
from traits.api import Float, Int

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController


class Model336TemperatureController(BaseLakeShoreController):
    input_c = Float
    input_d = Float
    setpoint3 = Float(auto_set=False, enter_set=True)
    setpoint3_readback = Float
    setpoint4 = Float(auto_set=False, enter_set=True)
    setpoint4_readback = Float

    def read_input_c(self, **kw):
        return self._read_input('c', self.units, **kw)

    def read_input_d(self, **kw):
        return self._read_input('d', self.units, **kw)

    def _setpoint3_changed(self, new):
        self.set_setpoint(new, 3)

    def _setpoint4_changed(self, new):
        self.set_setpoint(new, 4)

    def get_control_group(self):
        items = [Spring(height=10, springy=False)]
        for i, tag in enumerate('abcd'):
            idx = i + 1

            contents = []
            if self.iomap[i] is not None:
                contents = [Item('{}'.format(self.iomap[i])),
                            UItem('{}_readback'.format(self.iomap[i]), editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)]

            h = VGroup(Label(self.ionames[i]),
                       HGroup(Item('input_{}'.format(tag),
                                   style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)), *contents))
            items.append(h)

        grp = VGroup(*items)
        return grp

# ============= EOF =============================================
