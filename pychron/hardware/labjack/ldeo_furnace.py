# ===============================================================================
# Copyright 2018 Stephen Cox
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
import struct
import time

from pychron.hardware.core.core_device import CoreDevice

try:
    import LabJackPython
    import u3
except ImportError:
    print('Error loading LabJackPython driver')


class LamontFurnaceControl(CoreDevice):
    _device = None
    scl_pin = None
    sda_pin = None

    a_slope = None
    a_offset = None
    b_slope = None
    b_offset = None

    def __init__(self, *args, **kw):
        super(LamontFurnaceControl, self).__init__(*args, **kw)
        self.tc1_pin = 0  # 0 for AIN0, 2 for AIN2, etc
        self.tc2_pin = 1
        self.dac_pin = 2  # 0 for FIO4/5, 2 for FIO6/7 for steppers
        self._load_device()

    def to_double(self, buf):
        right, left = struct.unpack("<Ii", struct.pack("B" * 8, *buf[0:8]))
        return float(left) + float(right) / (2 ** 32)

    def _load_device(self):
        self._device = u3.U3()
        self.scl_pin = self.dac_pin + 4
        self.sda_pin = self.scl_pin + 1
        self._device.configIO(FIOAnalog=15, TimerCounterPinOffset=8)
        print('device SN is ', self._device.serialNumber)
        data = self._device.i2c(0x50, [64], NumI2CBytesToReceive=36, SDAPinNum=self.sda_pin, SCLPinNum=self.scl_pin)
        response = data['I2CBytes']
        print(response[0:8])
        self.a_slope = self.to_double(response[0:8])
        self.a_offset = self.to_double(response[8:16])
        self.b_slope = self.to_double(response[16:24])
        self.b_offset = self.to_double(response[24:32])

    def read_analog_in(self, pin):
        v = self._device.getAIN(pin)
        return v

    def readTC(self, number):
        temp = self.read_analog_in(number - 1) / .00004  # replace with actual TC table obviously
        return temp

    def extract(self, value, units=None, furnace=1):
        print(units)
        if not units == 'volts' or units == 'temperature':
            units = 'percent'

        self.info('set furnace output to {} {}'.format(value, units))
        if units == 'percent':
            value = value / 10
            if value < 0:
                self.warning('Consider changing you calibration curve. '
                             '{} percent converted to {}volts. Voltage must be positive'.format(value * 10, value))
                value = 0

        elif units == 'volts':
            if value > 10:
                self.warning('Did you mean to use percent units? '
                             '{} volts will set furnace to {}% output power.'.format(value, value * 10))
                value = 0

        elif units == 'temperature':
            minvalue = 100
            if value < minvalue:
                self.warning('Did you mean to use power control? '
                             '{} degrees is too low for the furnace.  Set to at least {} degrees.'.format(value,
                                                                                                          minvalue))
                value = 0
            self.warning('Temperature control not implemented')
            # Some PID control will be added later

        if furnace == 1:
            self._device.i2c(0x12, self._map_voltage(48, value, self.a_slope, self.a_offset),
                             SDAPinNum=self.sda_pin, SCLPinNum=self.scl_pin)
        elif furnace == 2:
            self._device.i2c(0x12, self._map_voltage(49, value, self.b_slope, self.b_offset),
                             SDAPinNum=self.sda_pin, SCLPinNum=self.scl_pin)
        else:
            self.warning('Invalid furnace number. Only outputs 1 and 2 available.')

    def _map_voltage(self, tag, value, slope, offset):
        a = int((value * slope + offset) / 256)
        b = int((value * slope + offset) % 256)
        return [tag, a, b]

    def drop_ball(self, position):
        positions = [[1, 5],
                     [1, 50],
                     [1, 80],
                     [1, 110],
                     [1, 140],
                     [1, 170],
                     [1, 200],
                     [1, 230],
                     [1, 260],
                     [1, 290],
                     [1, 320],
                     [1, 350]]

        stepper_number, runtime = positions[position - 1]
        if stepper_number == 1:
            self._run_stepper(runtime, 'forward', 5, 4)
            time.sleep(5)
            self._run_stepper(runtime + 3, 'backward', 5, 4)
        elif stepper_number == 2:
            self._run_stepper(runtime, 'forward', 4, 5)
            time.sleep(5)
            self._run_stepper(runtime + 3, 'backward', 4, 5)

    def _run_stepper(self, runtime, direction, a_id, b_id):
        dev = self._device
        if direction == 'forward':
            dev.getFeedback(u3.BitStateWrite(a_id, 0))
        else:
            dev.getFeedback(u3.BitStateWrite(a_id, 1))

        delay = 0.3

        st = time.time()
        while time.time() - st < runtime:
            dev.getFeedback(u3.BitStateWrite(b_id, 1))
            time.sleep(delay)
            dev.getFeedback(u3.BitStateWrite(b_id, 0))
            time.sleep(delay)


if __name__ == '__main__':
    testDev = LamontFurnaceControl()
    testDev.drop_ball(1)
    testDev.extract(3.1, units='volts', furnace=1)
    print(testDev.readTC(1))

# ============= EOF =============================================
