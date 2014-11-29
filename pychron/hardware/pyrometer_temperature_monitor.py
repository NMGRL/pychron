# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================



# =============enthought library imports=======================
from traits.api import Float
# =============standard library imports ========================

# =============local library imports  ==========================
from adc.adc_device import ADCDevice


class PyrometerTemperatureMonitor(ADCDevice):
    '''
    '''
    resistance = Float
    amps_max = Float
    amps_min = Float
    pyrometer_min = Float
    pyrometer_max = Float

    def load_additional_args(self, config):
        '''
        '''
        for s, k in [('General', 'resistance'),
                    ('General', 'amps_max'),
                    ('General', 'amps_min'),
                    ('General', 'pyrometer_min'),
                    ('General', 'pyrometer_max')]:
            self.set_attribute(config, k, s, k, cast='float')
#

        return True

    def _scan_(self, *args, **kw):
        '''

        '''
        vi = self._cdevice._scan_(*args, **kw)
        # print r
        # r=self.convert_voltage_temp(r/1000.0)
        # print r
        amps = vi / (1000 * self.resistance)
        temp = amps / (self.amps_max - self.amps_min) * (self.pyrometer_max - self.pyrometer_min) + self.pyrometer_min

        self.stream_manager.record(temp, self.name)

    def convert_voltage_temp(self, volt):
        '''
          
        '''

        # convert volts to current
        amps = volt / self.resistance

        # convert current to temperature
        return ((amps / (self.amps_max - self.amps_min)) * (self.pyrometer_max - self.pyrometer_min)) + self.pyrometer_min
