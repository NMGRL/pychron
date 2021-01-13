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
from pychron.hardware.adc.adc_device import PolynomialMapperMixin
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGaugeController
from pychron.hardware.labjack.base_u3_lv import BaseU3LV
from pychron.hardware.meter_calibration import MeterCalibration


class U3Gauge(BaseU3LV, BaseGaugeController, CoreDevice, PolynomialMapperMixin):

    def load_additional_args(self, config):
        BaseU3LV.load_additional_args(self, config)

        self.poly_mappers.append(self.factory(config, 'Conversion1'))
        self.poly_mappers.append(self.factory(config, 'Conversion2'))

        self._load_gauges(config)

        return True

    def _read_pressure(self, gauge):
        idx = self.gauges.index(gauge)
        v = self.read_adc_channel(idx)
        return self.poly_mappers[idx].map_measured(v)


# ============= EOF =============================================
