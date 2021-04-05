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
from traits.api import List
import math

from pychron.hardware.polyinomial_mapper import BaseMapper
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.base_controller import BaseGaugeController
from pychron.hardware.labjack.base_u3_lv import BaseU3LV

PARAMS = {'mbar': (6.8, 11.33),
          'ubar': (5.0, 8.333),
          'torr': (6.875, 11.46),
          'mtorr': (5.075, 8.458),
          'micron': (5.075, 8.458),
          'Pa': (5.6, 9.333),
          'kPa': (7.4, 12.33),
          }


class PressureMapper(BaseMapper):
    def map_measured(self, v):
        c, d = PARAMS[self.units]
        return 10 ** (1.667 * v - d)

    def map_output(self, v):
        c, d = PARAMS[self.units]
        return c + 0.6 * math.log10(v)


class U3GaugeController(BaseU3LV, BaseGaugeController, CoreDevice):
    poly_mappers = List

    def load_additional_args(self, config):
        BaseU3LV.load_additional_args(self, config)

        self.poly_mappers.append(self.mapper_factory(config, 'Conversion1'))
        self.poly_mappers.append(self.mapper_factory(config, 'Conversion2'))

        self._load_gauges(config)

        return True

    def mapper_factory(self, config, section):
        mapper = PressureMapper()
        units = self.config_get(config, section, 'units')
        mapper.units = units
        return mapper

    def _read_pressure(self, gauge, *args, **kw):
        idx = self.gauges.index(gauge)
        v = self.read_adc_channel(idx)
        return self.poly_mappers[idx].map_measured(v)

# ============= EOF =============================================
