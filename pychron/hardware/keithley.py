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
import time

from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.scpi_device import SCPIDevice


logging_setup('keithley')


class KeithleyMeter(CoreDevice):
    pass


class SCPIKeithley(SCPIDevice):
    def configure_instrument(self):
        pass


if __name__ == '__main__':
    d = SCPIKeithley(name='keithley617b')
    d.bootstrap()

    for i in range(10):
        d.get_measurement()

        time.sleep(0.5)

#============= EOF =============================================



