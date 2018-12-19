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
from traitsui.api import Group, Item, UItem, HGroup, VGroup, spring, Spring
from traits.api import Float

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController


class Model336TemperatureController(BaseLakeShoreController):

    input_c = Float
    input_d = Float
    setpoint3 = Float(auto_set=False, enter_set=True)
    setpoint3_readback = Float
    setpoint4 = Float(auto_set=False, enter_set=True)
    setpoint4_readback = Float

    def update(self, **kw):
        self.input_a = self.read_input_a(**kw)
        self.input_b = self.read_input_b(**kw)
        self.input_c = self.read_input_a(**kw)
        self.input_d = self.read_input_b(**kw)
        self.setpoint1_readback = self.read_setpoint(1)
        self.setpoint2_readback = self.read_setpoint(2)
        self.setpoint3_readback = self.read_setpoint(3)
        self.setpoint4_readback = self.read_setpoint(4)
        return self.input_a

    def setpoints_achieved(self, tol=1):
        v1 = self.read_input_a()
        if abs(v1 - self.setpoint1) < tol:
            self.debug('setpoint 1 achieved')
            v2 = self.read_input_b()
            if abs(v2 - self.setpoint2) < tol:
                self.debug('setpoint 2 achieved')
                v3 = self.read_input_c()
                if abs(v3 - self.setpoint3) < tol:
                    self.debug('setpoint 3 achieved')
                    v4 = self.read_input_d()
                    if abs(v4 - self.setpoint4) < tol:
                        self.debug('setpoint 4 achieved')
                        return True

    def set_setpoints(self, v1, v2, v3, v4):
        if v1 is not None:
            self.setpoint1 = v1
        if v2 is not None:
            self.setpoint2 = v2
        if v3 is not None:
            self.setpoint3 = v3
        if v4 is not None:
            self.setpoint4 = v4

    def read_input_c(self, **kw):
        return self._read_input('c', self.units, **kw)

    def read_input_d(self, **kw):
        return self._read_input('d', self.units, **kw)

    def _setpoint3_changed(self):
        self.set_setpoint(self.setpoint3, 3)

    def _setpoint4_changed(self):
        self.set_setpoint(self.setpoint4, 4)

    def get_control_group(self):
        grp = VGroup(Spring(height=10, springy=False), HGroup(Item('input_a', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint1'),
                           UItem('setpoint1_readback', editor=LCDEditor(width=120, height=30),
                                 style='readonly'), Spring(width=10, springy=False)),
                    HGroup(Item('input_b', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint2'),
                           UItem('setpoint2_readback', editor=LCDEditor(width=120, height=30),
                                 style='readonly'), Spring(width=10, springy=False)),
                    HGroup(Item('input_c', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint3'),
                           UItem('setpoint3_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False)),
                    HGroup(Item('input_d', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint4'),
                           UItem('setpoint4_readback', editor=LCDEditor(width=120, height=30),
                                  style='readonly'), Spring(width=10, springy=False))
                     )
        return grp

# ============= EOF =============================================
