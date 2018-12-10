import struct
import time

from pychron.hardware.core.core_device import CoreDevice

try:
    import LabJackPython
    import u3
except:
    print('Error loading LabJackPython driver')


class LamontFurnaceControl(CoreDevice):

    def __init__(self):
        self.TC1Pin = 0  # 0 for AIN0, 2 for AIN2, etc
        self.TC2Pin = 1
        self.dacPin = 2  # 0 for FIO4/5, 2 for FIO6/7 for steppers
        self.loadDevice()

    def toDouble(self, buffer):
        right, left = struct.unpack("<Ii", struct.pack("B" * 8, *buffer[0:8]))
        return float(left) + float(right) / (2 ** 32)

    def loadDevice(self):

        self.device = u3.U3()
        self.sclPin = self.dacPin + 4
        self.sdaPin = self.sclPin + 1
        self.device.configIO(FIOAnalog=15, TimerCounterPinOffset=8)
        print('device SN is ', self.device.serialNumber)
        data = self.device.i2c(0x50, [64], NumI2CBytesToReceive=36, SDAPinNum=self.sdaPin, SCLPinNum=self.sclPin)
        response = data['I2CBytes']
        print(response[0:8])
        self.aSlope = self.toDouble(response[0:8])
        self.aOffset = self.toDouble(response[8:16])
        self.bSlope = self.toDouble(response[16:24])
        self.bOffset = self.toDouble(response[24:32])

    def readAIN(self, pin):
        voltageAIN = self.device.getAIN(pin)
        return voltageAIN

    def readTC(self, number):
        temp = self.readAIN(number-1)/.00004 # replace with actual TC table obviously
        return temp

    def extract(self, value, units=None, furnace=1):
        print(units)
        if not units == 'volts' or units == 'temperature':
            units = 'percent'

        self.info('set furnace output to {} {}'.format(value, units))
        if units == 'percent':
            ovalue = value
            value = value/10
            if value < 0:
                self.warning('Consider changing you calibration curve. '
                             '{} percent converted to {}volts. Voltage must be positive'.format(ovalue, value))
                value = 0

        if units == 'volts':
            nvalue = value*10
            value = value
            if value > 10:
                self.warning('Did you mean to use percent units? '
                             '{} volts will set furnace to {}% output power.'.format(value, nvalue))
                value = 0

        if units == 'temperature':
            minvalue = 100
            value = value
            if value < minvalue:
                self.warning('Did you mean to use power control? '
                             '{} degrees is too low for the furnace.  Set to at least {} degrees.'.format(value, minvalue))
                value = 0
            self.warning('Temperature control not implemented')
            value = 0
            # Some PID control will be added later

        if furnace == 1:
            voltageA = value
            self.device.i2c(0x12, [48, int(((voltageA * self.aSlope) + self.aOffset) / 256),
                                   int(((voltageA * self.aSlope) + self.aOffset) % 256)],
                            SDAPinNum=self.sdaPin, SCLPinNum=self.sclPin)
        elif furnace == 2:
            voltageB = value
            self.device.i2c(0x12, [49, int(((voltageB * self.bSlope) + self.bOffset) / 256),
                                   int(((voltageB * self.bSlope) + self.bOffset) % 256)],
                            SDAPinNum=self.sdaPin, SCLPinNum=self.sclPin)
        else:
            self.warning('Invalid furnace number. Only outputs 1 and 2 available.')

    def drop_ball(self, position):
        position_dict = {
            1: [1, 5],
            2: [1, 50],
            3: [1, 80],
            4: [1, 110],
            5: [1, 140],
            6: [1, 170],
            7: [1, 200],
            8: [1, 230],
            9: [1, 260],
            10: [1, 290],
            11: [1, 320],
            12: [1, 350]
        }
        stepper_number = position_dict[position][0]
        runtime = position_dict[position][1]
        if stepper_number == 1:
            self.run_stepper_1(runtime, 'forward')
            time.sleep(5)
            self.run_stepper_1(runtime + 3, 'backward')
        elif stepper_number == 2:
            self.run_stepper_2(runtime, 'forward')
            time.sleep(5)
            self.run_stepper_2(runtime + 3, 'backward')

    def run_stepper_1(self, runtime, direction):
        timestop = time.time() + runtime
        if direction == 'forward':
            self.device.getFeedback(u3.BitStateWrite(5, 0))
        else:
            self.device.getFeedback(u3.BitStateWrite(5, 1))
        while time.time() < timestop:
            self.device.getFeedback(u3.BitStateWrite(4, 1))
            time.sleep(.03)
            self.device.getFeedback(u3.BitStateWrite(4, 0))
            time.sleep(.03)

    def run_stepper_2(self, runtime, direction):
        timestop = time.time() + runtime
        if direction == 'forward':
            self.device.getFeedback(u3.BitStateWrite(4, 0))
        else:
            self.device.getFeedback(u3.BitStateWrite(4, 1))
        while time.time() < timestop:
            self.device.getFeedback(u3.BitStateWrite(5, 1))
            time.sleep(.03)
            self.device.getFeedback(u3.BitStateWrite(5, 0))
            time.sleep(.03)

testDev = LamontFurnaceControl()
testDev.drop_ball(1)
testDev.extract(3.1, units='volts', furnace=1)
print(testDev.readTC(1))
