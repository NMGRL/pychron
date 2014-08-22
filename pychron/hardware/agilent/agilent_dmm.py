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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class AgilentDMM(CoreDevice):
    """
    class for interfacing with an Agilent DMM - most likely a
    34401A. Since they use SCPI
    http://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments
    model number is not very important?

    """
    def initialize(self, *args, **kw):
        """
        configure instrument
        """
        self.tell('*RST')
        self.tell('*CLS')

        #configure
        self.tell('VOLT:DC:RES MAX')

        #look into what these are for
        self.tell(':ZERO:AUTO OFF')
        self.tell(':INP:IMP:AUTO ON')

    def trigger(self):
        """
            trigger a measurement. should be followed by a FETCH? (AgilentDMM.get_value)

        """
        self.debug('triggering measurement')
        self.ask('TRIGGER')

    def get_value(self):
        """
            return a value read from the device
        """
        if self.simulation:
            v= 0
        else:
            self.trigger()
            v = self.ask('FETCH?')

        v = self._parse_response(v)
        return v

    # def _parse_response(self, v):
    #     pass

#============= EOF =============================================



