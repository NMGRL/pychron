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
from pychron.hardware.core.scpi_device import SCPIDevice


class KeithleyMeter(CoreDevice):
    pass


class SCPIKeithley(SCPIDevice):
    def zero(self):
        self.debug('Turn zero-check on')
        self.tell('SYST:ZCH ON')

        self.debug('Turn zero-correct on')
        self.tell('SYST:ZCOR ON')

        self.debug('Turn zero-check off')
        self.tell('SYST:ZCH OFF')

    def configure_instrument(self):

        # self.tell('SYST:ZCH ON')
        # self.tell('TRIG:COUNT INF;SOUR TIM;TIM 0.1')
        # self.tell('TRIG:SOUR TIM')
        # self.tell('TRIG:TIM 0.1')

        # self.tell('SYST:ZCH OFF')
        # self.tell('SYST:ZCOR ON')
        self.tell('VOLT:RANG:AUTO ON')

        self.zero()

        # setup counting
        self.tell('ARM:LAY2:SOUR IMM')
        self.tell('TRIG:COUNT INF')
        self.tell('INIT')

        # self.tell('VOLT:RANG:AUTO OFF')
        # self.tell('SENS:VOLT:RANG 20')
        # self.tell('STAT:PRES')
    # def get_measurement(self):
    #     print self.ask('read?')

if __name__ == '__main__':
    import time
    from pychron.paths import paths
    from pychron.core.helpers.logger_setup import logging_setup
    paths.build('_dev')
    logging_setup('keithley')

    d = SCPIKeithley(name='keithley617b')
    d.bootstrap()

    # time.sleep(1)
    # d.identify_instrument()
    for i in range(100):
        d.get_measurement()

        time.sleep(1)

# ============= EOF =============================================



