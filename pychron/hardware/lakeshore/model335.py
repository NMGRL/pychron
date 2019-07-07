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

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController


class Model335TemperatureController(BaseLakeShoreController):
    def get_control_group(self):
        grp = VGroup(Spring(height=10, springy=False), HGroup(Item('input_a', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint1'),
                           UItem('setpoint1_readback', editor=LCDEditor(width=120, height=30),
                                 style='readonly'), Spring(width=10, springy=False)),
                    HGroup(Item('input_b', style='readonly', editor=LCDEditor(width=120, ndigits=6, height=30)),
                           Item('setpoint2'),
                           UItem('setpoint2_readback', editor=LCDEditor(width=120, height=30),
                                 style='readonly'), Spring(width=10, springy=False)))
        return grp

# ============= EOF =============================================
