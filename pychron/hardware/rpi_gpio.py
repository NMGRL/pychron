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
from pychron.hardware.actuators.gp_actuator import GPActuator

try:
    import RPi.GPIO as GPIO
except ImportError:
    class DummyGPIO:
        OUT = 0
        IN = 0
        BCM = 0

        def setmode(self, *args):
            pass

        def setwarnings(self, *args):
            pass

        def setup(self, *args):
            pass

        def output(self, *args):
            pass

        def input(self, *args):
            pass

        def close(self):
            pass


    GPIO = DummyGPIO()

# ============= standard library imports ========================
# ============= local library imports  ==========================


class RPiGPIO(GPActuator):
    def open(self, *args, **kw):
        if not isinstance(GPIO, DummyGPIO):
            self.simulation = False
        return True

    def close(self):
        GPIO.close()
        super(RPiGPIO, self).close()

    def load_additional_args(self, config):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        outpins = self.config_get(config, 'Pins', 'output')
        inpins = self.config_get(config, 'Pins', 'input')
        for pins, mode in ((outpins, GPIO.OUT),
                           (inpins, GPIO.IN)):
            for pin in pins:
                GPIO.setup(pin, mode)

    def open_channel(self, channel, **kw):
        GPIO.output(channel, 0)
        return True

    def close_channel(self, channel, **kw):
        GPIO.output(channel, 1)
        return True

    def get_channel_state(self, channel, **kw):
        return GPIO.input(channel)

# ============= EOF =============================================
