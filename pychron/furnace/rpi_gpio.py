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
try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class RPiGPIO(CoreDevice):
    def close(self):
        GPIO.close()
        super(RPiGPIO, self).close()

    def load_additional_args(self, config):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        outpins = self.config_get('Pins', 'output')
        inpins = self.config_get('Pins', 'input')
        for mode, pins in ((outpins, GPIO.OUT),
                           (inpins, GPIO.IN)):
            for pin in pins:
                GPIO.setup(pin, mode)

    def open_channel(self, channel):
        GPIO.output(channel, 0)

    def close_channel(self, channel):
        GPIO.output(channel, 1)

    def get_channel_state(self, channel):
        return GPIO.input(channel)

# ============= EOF =============================================
