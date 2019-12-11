# ===============================================================================
# Copyright 2019 ross
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
from traitsui.api import View, Item, Group, ListEditor, InstanceEditor

from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGauge, BaseGaugeController


class BaseQtegraGaugeController(BaseGaugeController, CoreDevice):
    gauge_klass = BaseGauge
    scan_func = 'update_pressures'

    def initialize(self, *args, **kw):
        return True

    def get_pressures(self, verbose=False):
        # this could be moved to BaseGaugeController
        self.update_pressures()
        return [g.pressure for g in self.gauges]

    def load_additional_args(self, config, *args, **kw):
        self.display_name = self.config_get(config, 'General', 'display_name', default=self.name)
        # self.mode = self.config_get(config, 'Communications', 'mode', default='rs485')
        self._load_gauges(config)
        return True

    def gauge_view(self):
        v = View(Group(Item('gauges', style='custom',
                            show_label=False,
                            editor=ListEditor(mutable=False,
                                              style='custom',
                                              editor=InstanceEditor())),
                       show_border=True,
                       label=self.display_name))
        return v


class QtegraGaugeController(BaseQtegraGaugeController):
    def _read_pressure(self, name=None, verbose=False):
        pressure = 'err'
        if name is not None:
            gauge = name
            if isinstance(gauge, str):
                gauge = self.get_gauge(name)
            gauge_name = name
            if gauge_name and isinstance(gauge_name,BaseGauge):
                gauge_name = gauge_name.name
            pressure = self.ask('GetParameter {} Readback'.format(gauge_name), verbose=verbose)
            if pressure and pressure.startswith('>'): # This line and the next could go, I suppose.
                pressure = pressure[1:]

        return pressure or 'err'
# ============= EOF =============================================
