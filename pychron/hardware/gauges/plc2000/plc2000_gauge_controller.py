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
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.modbus import ModbusMixin
from pychron.hardware.gauges.base_controller import BaseGaugeController


class PLC2000GaugeController(BaseGaugeController, CoreDevice, ModbusMixin):
    def load_additional_args(self, config, *args, **kw):
        self.display_name = self.config_get(
            config, "General", "display_name", default=self.name
        )
        self._load_gauges(config)
        return True

    def get_pressures(self, *args, **kw):
        kw["force"] = True
        return super(PLC2000GaugeController, self).get_pressures(*args, **kw)

    def _read_pressure(self, name=None, verbose=False):
        pressure = "err"

        if isinstance(name, str):
            gauge = self.get_gauge(name)
            channel = gauge.channel
        else:
            channel = name.channel

        if name is not None:
            # register = channel-1
            register = int(channel) - 1
            try:
                pressure = self._read_float(register)
            except BaseException as e:
                self.debug_exception()
                self.debug("failed reading register={}, error={}".format(register, e))
        return pressure


# ============= EOF =============================================
