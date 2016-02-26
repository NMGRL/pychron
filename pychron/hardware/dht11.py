# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Str, Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.headless_config_loadable import HeadlessConfigLoadable

try:
    from Adafruit_DHT import read_retry, DHT11
except ImportError:
    DHT11 = None


    def read_retry(sensor, pin):
        return None, None


class DHT11(HeadlessConfigLoadable):
    pin = Int
    units = Str

    _humidity = 0
    _temperature = 0
    _sensor = None

    def load_additional_args(self, config):
        self.set_attribute(config, 'pin', 'General', 'pin', cast='int')
        self.set_attribute(config, 'units', 'General', 'units')

    def initialize(self, *args, **kw):
        self._sensor = DHT11

    def update(self):
        self._humidity, temp = read_retry(self._sensor, self.pin)
        if self.units == 'F':
            temp = temp * 9 / 5. + 32
        self._temperature = temp
        self.debug('update temp={}, hum={}'.format(temp, self._humidity))

    @property
    def humidity(self):
        return self._humidity

    @property
    def temperature(self):
        return self._temperature

# ============= EOF =============================================
