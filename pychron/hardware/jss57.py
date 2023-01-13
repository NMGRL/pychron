from pychron.hardware.base_linear_drive import BaseLinearDrive
from pychron.hardware.core.core_device import CoreDevice
from pychron.loggable import Loggable
from pychron.paths import paths
from traits.api import Instance, HasTraits, Str, Int
import time


class LinearDrive(CoreDevice):
    stepsperdata = Int(20000)
    data_position = 0

    def set_position(self, data=None, steps=None, block=True, use_absolute=False):
        if data is not None:
            self.data_position = data
            v = int(data * self.stepsperdata)
        elif steps is not None:
            v = steps

        self._set_motor(v, use_absolute)
        if block:
            self.block()

    def _set_motor(self, v, use_absolute):
        raise NotImplementedError

    def block(self, n=2, tolerance=1, progress=None, homing=False, verbose=False, timeout=30):
        c = 0
        st = time.time()
        while 1:
            if self.simulation:
                break

            if time.time() - st > timeout:
                break

            if self.moving():
                self._update_position()
                continue

            c += 1
            if c > n:
                break

            time.sleep(0.1)


class STP_MTRD(LinearDrive):
    address = Str('1')
    mmperturn = 25
    nominal_home_position = 0.75

    def test(self):
        self.debug('asdfsadf')
        self.ask('1PM')
        resp = self.ask('1MV')
        self._update_position()
        self.set_position(2)
        time.sleep(1)
        self.set_position(-1.5)
        #
        # self.move_mm(-2)
        #
        # time.sleep(1)
        # self.move_mm(2)
        
    def move_mm(self, mm):
        self.set_position(mm/self.mmperturn)

    def initialize(self):
        self._set_acceleration(2.5)
        self._set_velocity(0.25)

        # homing
        # setup digital inputs
        self.ask('DL3')

    def home(self):
        # set distance to -1 to set direction of seek home
        self.ask('DI-1')

        # seek home
        self.ask('SH1H')
        self.block()

        # set encoder position to 0
        self.ask('EP0')
        # set position to 0
        self.ask('SP0')

        # move to nominal position
        self.set_absolute_position(self.nominal_home_position)

    def set_absolute_position(self, v, **kw):
        self.set_position(v, use_absolute=True, **kw)

    def moving(self):
        sc = self._read_status_code()
        _, v = sc.split('=')
        return int(v, 16) > 16  # moving \x0010

    def _update_position(self):
        pos = self._read_motor_position()
        self.debug(f'current motor position = {pos}')

    def _read_status_code(self):
        return self.ask('SC')

    def _read_motor_position(self, *args, **kw):
        resp = self.ask('IE')
        _, v = resp.split('=')
        return int(v, 16)

    def _set_acceleration(self, v):
        self.ask(f'AC{v}')
        self.ask(f'DE{v}')

    def _set_velocity(self, v):
        self.ask(f'VE{v}')

    def ask(self, cmd, *args, **kw):
        return super(STP_MTRD, self).ask(f"{self.address}{cmd}", *args, **kw)

    def _set_motor(self, value, use_absolute):
        if use_absolute:
            self.ask(f'DI{value}')
            self.ask('FP')
        else:
            self.ask(f'FL{value}')

        # cmds = ['1IFH','1BR1','1JA10', '1JL10', '1JS1',]
        # for cmd in cmds:
        #     self.ask(cmd)

        # cmds = [ '1CJ', '1CS-1', '1SJ']
        # for cmd in cmds:
        #     self.ask(cmd)
        #     for i in range(3):
        #         self.ask('1IE')
        #         time.sleep(1)


if __name__ == '__main__':
    paths.build('~/Pychron')
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup("motor")

    dev = STP_MTRD(name='focusmotor')
    dev.bootstrap()
    print('asdf')
    # dev.test()
