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
from threading import Thread

from pychron.hardware.core.core_device import CoreDevice

try:
    import LabJackPython
    import u3
except ImportError:
    print("Error loading LabJackPython driver")


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
        self.furnace = 1  # defaults to furnace output 1

    def to_double(self, buf):
        right, left = struct.unpack("<Ii", struct.pack("B" * 8, *buf[0:8]))
        return float(left) + float(right) / (2**32)

    def return_sn(self):
        return self._device.serialNumber

    def load(self, *args, **kw):
        return True

    def open(self, *args, **kw):
        try:
            self._device = u3.U3()
        except BaseException:
            self.warning("failed to create U3 device")
            return
        return True

    def initialize(self, *args, **kw):
        self.scl_pin = self.dac_pin + 4
        self.sda_pin = self.scl_pin + 1
        self._device.getFeedback(
            u3.BitStateWrite(4, 0)
        )  # write both sleep lines low to prevent stepper from moving on load
        self._device.getFeedback(
            u3.BitStateWrite(5, 0)
        )  # write both sleep lines low to prevent stepper from moving on load
        self._device.configIO(
            FIOAnalog=15, NumberOfTimersEnabled=2, TimerCounterPinOffset=8
        )
        self._device.configTimerClock(
            TimerClockBase=3, TimerClockDivisor=50
        )  # 3 = 1 Mhz; 50 ==> 1/50 = 20 kHz
        self._device.getFeedback(
            u3.Timer0Config(TimerMode=7, Value=100)
        )  # FreqOut mode; Value 20 gives (20 kHz)/(2*100) = 100 Hz
        self._device.getFeedback(
            u3.Timer1Config(TimerMode=7, Value=100)
        )  # FreqOut mode; Value 20 gives (20 kHz)/(2*100) = 100 Hz
        print("device SN is ", self._device.serialNumber)
        data = self._i2c(0x50, [64], NumI2CBytesToReceive=36)
        response = data["I2CBytes"]
        print(response[0:8])
        self.a_slope = self.to_double(response[0:8])
        self.a_offset = self.to_double(response[8:16])
        self.b_slope = self.to_double(response[16:24])
        self.b_offset = self.to_double(response[24:32])

        self.test_connection()

    def test_connection(self):

        sn = self.return_sn()
        if 256 <= sn <= 2147483647:
            self.info("Labjack loaded")
            ret = True
            err = ""

        else:
            self.warning("Invalid Labjack serial number: check Labjack connection")
            ret = False
            err = "Invalid Labjack serial number: check Labjack connection"

        return ret, err

    def read_analog_in(self, pin):
        v = self._device.getAIN(pin)
        return v

    def readTC(self, number):
        temp = (
            self.read_analog_in(number - 1) / 0.00004
        )  # replace with actual TC table obviously
        return temp

    def extract(self, value, units=None, furnace=1):

        self.furnace = furnace

        print(units)
        if not units == "volts" or units == "temperature":
            units = "percent"

        self.info("set furnace output to {} {}".format(value, units))
        if units == "percent":
            value = value / 10
            if value < 0:
                self.warning(
                    "Consider changing you calibration curve. "
                    "{} percent converted to {}volts. Voltage must be positive".format(
                        value * 10, value
                    )
                )
                value = 0

        elif units == "volts":
            if value > 10:
                self.warning(
                    "Did you mean to use percent units? "
                    "{} volts will set furnace to {}% output power.".format(
                        value, value * 10
                    )
                )
                value = 0

        elif units == "temperature":
            minvalue = 100
            if value < minvalue:
                self.warning(
                    "Did you mean to use power control? "
                    "{} degrees is too low for the furnace.  Set to at least {} degrees.".format(
                        value, minvalue
                    )
                )
                value = 0
            self.warning("Temperature control not implemented")
            # Some PID control will be added later

        self.set_furnace_setpoint(value)

    def set_furnace_setpoint(self, value, furnace=1):
        # this function can be called separately from extract if another script is performing the units logic
        self.furnace = furnace

        if self.furnace == 1:
            v = self._map_voltage(48, value, self.a_slope, self.a_offset)
            self._i2c(0x12, v)
        elif self.furnace == 2:
            v = self._map_voltage(49, value, self.b_slope, self.b_offset)
            self._i2c(0x12, v)
        else:
            self.warning("Invalid furnace number. Only outputs 1 and 2 available.")

    def _i2c(self, address, value, **kw):
        return self._device.i2c(
            address, value, SDAPinNum=self.sda_pin, SCLPinNum=self.scl_pin, **kw
        )

    def _map_voltage(self, tag, value, slope, offset):
        m = value * slope + offset
        a = int(m / 256)
        b = int(m % 256)
        return [tag, a, b]

    # def _unmap_voltage(self, tag, a, b, slope, offset):
    #     m = a*256 + b
    #     value = (m - offset)/slope
    #     return [tag, value]

    def drop_ball(self, position):
        def func():
            self.goto_ball(position)
            time.sleep(5)
            self.returnfrom_ball(position)

        t = Thread(target=func)
        t.start()

    def goto_ball(self, position):
        positions = [
            [1, 5],
            [1, 10],
            [1, 15],
            [1, 20],
            [1, 25],
            [1, 30],
            [1, 200],
            [1, 230],
            [1, 260],
            [1, 290],
            [1, 320],
            [1, 350],
        ]

        stepper_number, runtime = positions[position - 1]

        self.info(
            "Going to position {}; running for {} seconds".format(position, runtime)
        )

        if position == 0:  # position command zero does nothing
            runtime = 0

        if stepper_number == 1:
            a, b = 5, 4
        elif stepper_number == 2:
            a, b = 4, 5

        self._run_stepper(runtime, "forward", a, b)
        time.sleep(runtime)

    def returnfrom_ball(self, position):
        positions = [
            [1, 5],
            [1, 10],
            [1, 15],
            [1, 20],
            [1, 25],
            [1, 30],
            [1, 200],
            [1, 230],
            [1, 260],
            [1, 290],
            [1, 320],
            [1, 350],
        ]

        stepper_number, runtime = positions[position - 1]

        if position == 0:  # position command zero returns all the way
            runtime = max([t for motor, t in positions])

        if stepper_number == 1:
            a, b = 5, 4
        elif stepper_number == 2:
            a, b = 4, 5

        self._run_stepper(runtime + 3, "backward", a, b)
        time.sleep(runtime)

    def get_process_value(self):
        # note it is not possible to read the current setting for the LJTick-DAC, so we must measure voltage
        if self.furnace == 1:
            pv = self.read_analog_in(
                2
            )  # assumes LJTick-DAC first channel is wired to AIN 2
        elif self.furnace == 2:
            pv = self.read_analog_in(
                3
            )  # assumes LJTick-DAC first channel is wired to AIN 3
        else:
            self.warning("Invalid furnace number. Only outputs 1 and 2 available.")
        return pv

    def get_summary(self):
        summary = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "OP1": self.read_analog_in(2),
            "TC1": self.readTC(1),
            "OP2": self.read_analog_in(3),
            "TC2": self.readTC(2),
        }
        return summary

    def _run_stepper(self, runtime, direction, a_id, b_id):
        def func():
            dev = self._device
            if direction == "forward":
                dev.getFeedback(u3.BitStateWrite(a_id, 0))
            else:
                dev.getFeedback(u3.BitStateWrite(a_id, 1))

            # st = time.time()
            dev.getFeedback(u3.BitStateWrite(b_id, 1))
            time.sleep(runtime)
            self.info("adjk;fdsajf ", runtime)
            # while time.time() - st < runtime:
            #     time.sleep(1)

            dev.getFeedback(u3.BitStateWrite(b_id, 0))

        t = Thread(target=func)
        t.start()


if __name__ == "__main__":
    testDev = LamontFurnaceControl()
    testDev.drop_ball(1)
    testDev.extract(3.1, units="volts", furnace=1)
    print(testDev.readTC(1))

# ============= EOF =============================================
