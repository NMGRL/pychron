# ===============================================================================
# Copyright 2017 ross
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


class BaseVarianGaugeController(BaseGaugeController, CoreDevice):
    def load_additional_args(self, config, *args, **kw):
        self.address = self.config_get(config, 'General', 'address', optional=False)
        self.display_name = self.config_get(config, 'General', 'display_name', default=self.name)
        # self.mode = self.config_get(config, 'Communications', 'mode', default='rs485')
        self._load_gauges(config)
        return True


class XGS600GaugeController(BaseVarianGaugeController):
    def _read_pressure(self, name=None, verbose=False):
        pressure = 'err'
        if name is not None:
            gauge = name
            if isinstance(gauge, str):
                gauge = self.get_gauge(name)
            channel = gauge.channel
            cmd = '#{}02U{}'.format(self.address, channel)
            pressure = self.ask(cmd, verbose=verbose)
            if pressure and pressure.startswith('>'):
                pressure = pressure[1:]

        return pressure or 'err'
# ============= EOF =============================================
