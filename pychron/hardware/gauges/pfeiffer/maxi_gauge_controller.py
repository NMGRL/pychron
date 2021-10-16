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
import six
from traitsui.api import View, Item, Group, ListEditor, InstanceEditor

from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGauge, BaseGaugeController


class PfeifferMaxiGaugeController(BaseGaugeController, CoreDevice):
    def _read_pressure(self, name=None, verbose=False):
        if name is None:
            name = "Z"
        else:
            if isinstance(name, str):
                gauge = self.get_gauge(name)
                name = gauge.channel
            else:
                name = name.channel

        pressure = "err"
        if name:
            cmd = "PR{}".format(name)
            r = self.ask(cmd, verbose=verbose)
            if chr(6) in r:
                cmd = "\x05"
                oterminator = self.communicator.write_terminator
                self.communicator.write_terminator = None
                r = self.ask(cmd, verbose=verbose)
                self.communicator.write_terminator = oterminator
                # pressure = r.split(',')[1].rstrip('\r\n')
                try:
                    pressure = r.split(",")[1].rstrip()
                except IndexError:
                    pressure = "err"

        return pressure

    def load_additional_args(self, config, *args, **kw):
        self.address = self.config_get(config, "General", "address", optional=False)
        self.display_name = self.config_get(
            config, "General", "display_name", default=self.name
        )
        # self.mode = self.config_get(config, 'Communications', 'mode', default='rs485')
        self._load_gauges(config)
        return True


# ============= EOF =============================================
