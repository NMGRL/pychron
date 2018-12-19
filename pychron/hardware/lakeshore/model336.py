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

    def update(self, **kw):
        for tag in 'abcd':
            func = getattr(self, 'read_input_{}'.format(tag))
            v = func(**kw)
            setattr(self, 'input_{}'.format(tag), v)

        # self.input_a = self.read_input_a(**kw)
        # self.input_b = self.read_input_b(**kw)
        # self.input_c = self.read_input_a(**kw) # should this be self.read_input_c?
        # self.input_d = self.read_input_b(**kw) # should this be self.read_input_d?

        for tag in (1, 2, 3, 4):
            v = self.read_setpoint(tag)
            setattr(self, 'setpoint{}_readback'.format(tag), v)

        # self.setpoint1_readback = self.read_setpoint(1)
        # self.setpoint2_readback = self.read_setpoint(2)
        # self.setpoint3_readback = self.read_setpoint(3)
        # self.setpoint4_readback = self.read_setpoint(4)
        return self.input_a

    def setpoints_achieved(self, tol=1):

        for i, tag in enumerate('abcd'):
            idx = i + 1
            v = self._read_input(tag, self.units)
            setpoint = getattr(self, 'setpoint{}'.format(idx))
            if abs(v - setpoint) > tol:
                return
            else:
                self.debug('setpoint {} achieved'.format(idx))

        return True
        #
        # v1 = self.read_input_a()
        # if abs(v1 - self.setpoint1) < tol:
        #     self.debug('setpoint 1 achieved')
        #     v2 = self.read_input_b()
        #     if abs(v2 - self.setpoint2) < tol:
        #         self.debug('setpoint 2 achieved')
        #         v3 = self.read_input_c()
        #         if abs(v3 - self.setpoint3) < tol:
        #             self.debug('setpoint 3 achieved')
        #             v4 = self.read_input_d()
        #             if abs(v4 - self.setpoint4) < tol:
        #                 self.debug('setpoint 4 achieved')
        #                 return True

    def set_setpoints(self, *setpoints):
        for i, v in enumerate(setpoints):
            if v is not None:
                idx = i+1
                setattr(self, 'setpoint{}'.format(idx), v)

        # if v1 is not None:
        #     self.setpoint1 = v1
        # if v2 is not None:
        #     self.setpoint2 = v2
        # if v3 is not None:
        #     self.setpoint3 = v3
        # if v4 is not None:
        #     self.setpoint4 = v4

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
            if self.iomap[i] is not 'None':
                setpoint_content_1 = Item('{}'.format(self.iomap[i]))
                setpoint_content_2 = UItem('setpoint{}_readback'.format(idx), editor=LCDEditor(width=120, height=30),
                                    style='readonly'), Spring(width=10, springy=False)
            else:
                setpoint_content_1 = []
                setpoint_content_2 = []
            h = VGroup(Label(self.ionames[i]), HGroup(Item('input_{}'.format(tag), style='readonly',
                            editor=LCDEditor(width=120, ndigits=6, height=30)),
                            setpoint_content_1, setpoint_content_2))
            items.append(h)

        # grp = VGroup(Spring(height=10, springy=False),
        #              ,
        #              HGroup(Item('input_b', style='readonly', editor=lcd_editor),
        #                     Item('setpoint3'),
        #                     UItem('setpoint3_readback', editor=read_back_editor,
        #                           style='readonly'), Spring(width=10, springy=False)),
        #              HGroup(Item('input_c', style='readonly', editor=lcd_editor),
        #                     Item('setpoint2'),
        #                     UItem('setpoint2_readback', editor=read_back_editor,
        #                           style='readonly'), Spring(width=10, springy=False)),
        #              HGroup(Item('input_d', style='readonly', editor=lcd_editor),
        #                     Item('setpoint4'),
        #                     UItem('setpoint4_readback', editor=read_back_editor,
        #                           style='readonly'), Spring(width=10, springy=False)))

        grp = VGroup(*items)
        return grp

# ============= EOF =============================================
