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
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGaugeController


class QtegraGaugeController(BaseGaugeController, CoreDevice):
    def load_additional_args(self, config, *args, **kw):
        self.display_name = self.config_get(
            config, "General", "display_name", default=self.name
        )
        self._load_gauges(config)
        return True

    def get_pressures(self, *args, **kw):
        kw["force"] = True
        return super(QtegraGaugeController, self).get_pressures(*args, **kw)

    def _read_pressure(self, name=None, verbose=False):
        pressure = "err"

        if isinstance(name, str):
            gauge = self.get_gauge(name)
            name = gauge.name
        else:
            name = name.name

        if name is not None:
            pressure = self.ask("GetParameter {}".format(name), verbose=True)

        return pressure


# ============= EOF =============================================
