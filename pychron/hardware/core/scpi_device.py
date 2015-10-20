# ===============================================================================
# Copyright 2014 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class SCPIDevice(CoreDevice):
    def initialize(self, *args, **kw):
        """
            initialize instrument
        """
        self.tell('*RST')
        self.configure_instrument()
        self.tell('*CLS')

    def identify_instrument(self):
        v =self.ask('*IDN?')
        self.info('Instrument ID {}'.format(v))

    def configure_instrument(self):
        """
            subclass should define this method
        """
        raise NotImplementedError

    def trigger(self):
        """
            trigger a measurement. should be followed by a FETCH? (AgilentDMM.get_value)

        """
        self.debug('triggering measurement')
        self.tell('INIT')

    def get_measurement(self):
        """
            return a value read from the device
        """
        if self.simulation:
            self.debug('simulation')
            v= 0
        else:
            v = self.ask('FETCH?')

        v = self._parse_response(v)
        self.debug('get_measurment. value = {}'.format(v))
        return v
# ============= EOF =============================================



