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
from traitsui.api import Group, Item, UItem, HGroup

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.lakeshore.base_controller import BaseLakeShoreController


class Model335TemperatureController(BaseLakeShoreController):
    def get_control_group(self):
        grp = Group(Item('input_a', style='readonly', editor=LCDEditor(width=200, ndigits=6, height=30)),
                    Item('input_b', style='readonly', editor=LCDEditor(width=200, ndigits=6, height=30)),
                    HGroup(Item('setpoint1'),
                           UItem('setpoint1_readback', editor=LCDEditor(width=200, height=30),
                                 style='readonly')))
        return grp

# ============= EOF =============================================
