# ===============================================================================
# Copyright 2021 ross
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
from traits.api import Float, Int, Str
from traitsui.api import View, Item, UItem, HGroup, UReadonly

from pychron.core.ui.color_map_bar_editor import BarGaugeEditor
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice


class SPCIonPumpController(CoreDevice):
    scan_func = 'update'

    pressure = Float

    address = Int
    display_name = Str
    low = 1e-10
    high = 1e-7

    def load_additional_args(self, config):
        self.set_attribute(config, 'General', 'address', cast='int')
        self.set_attribute(config, 'General', 'display_name')

        return True

    def update(self):
        self.get_pressure()

    def get_pressure(self):
        r = self._read_pressure()
        self.pressure = r

        return self.pressure

    @get_float(0)
    def _read_pressure(self):
        cmd = self._make_command('0B')
        return self.ask(cmd)

    def _make_command(self, cmd):
        return '~ {:02X} {} 00'.format(self.address, cmd)

    def pump_view(self):
        v = View(HGroup(UReadonly('display_name', width=-30, ),
                        Item('pressure',
                             format_str='%0.2e',
                             show_label=False,
                             style='readonly'),
                        Item('pressure',
                             show_label=False,
                             width=self.width,
                             editor=BarGaugeEditor(low=1e-10,
                                                   high=1e-7,
                                                   scale='power',
                                                   color_scalar=1))))

        return v
# ============= EOF =============================================
