# ===============================================================================
# Copyright 2018 ross
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
from __future__ import absolute_import
from traits.api import Enum, Float, Property
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice
import re

IDN_RE = re.compile(r'\w{4},\w{8},\w{7}\/[\w\#]{7},\d.\d')


class BaseLakeShoreController(CoreDevice):
    units = Enum('C', 'K')
    scan_func = 'update'

    input_a = Float
    input_b = Float
    setpoint1 = Float(auto_set=False, enter_set=True)
    setpoint1_readback = Float
    setpoint2 = Float(auto_set=False, enter_set=True)
    setpoint2_readback = Float

    def load_additional_args(self, config):
        self.set_attribute(config, 'units', 'General', 'units', default='K')
        return True

    def initialize(self, *args, **kw):
        self.communicator.write_terminator = chr(10)  # line feed \n
        return super(BaseLakeShoreController, self).initialize(*args, **kw)

    def test_connection(self):
        self.tell('*CLS')
        resp = self.ask('*IDN?')
        return bool(IDN_RE.match(resp))

    def update(self, **kw):
        self.input_a = self.read_input_a(**kw)
        self.input_b = self.read_input_b(**kw)
        self.setpoint1_readback = self.read_setpoint(1)
        self.setpoint2_readback = self.read_setpoint(2)
        return self.input_a

    def setpoints_achieved(self, tol=1):
        v1 = self.read_input_a()
        if abs(v1 - self.setpoint1) < tol:
            v2 = self.read_input_a()
            if abs(v2 - self.setpoint2) < tol:
                return self.setpoints_achieved_cnt

    @get_float(default=0)
    def read_setpoint(self, output, verbose=False):
        return self.ask('SETP? {}'.format(output), verbose=verbose)

    def set_setpoints(self, v1, v2):
        # self.set_setpoint(v1, 1)
        self.setpoint1 = v1
        if v2 is not None:
            self.setpoint2 = v2

    def set_setpoint(self, v, output=1):
        self.tell('SETP {},{}'.format(output, v))

    def read_input(self, v, **kw):
        if isinstance(v, int):
            v = 'ab'[v - 1]
        return self._read_input(v, self.units, **kw)

    def read_input_a(self, **kw):
        return self._read_input('a', self.units, **kw)

    def read_input_b(self, **kw):
        return self._read_input('b', self.units, **kw)

    @get_float(default=0)
    def _read_input(self, tag, mode='C', verbose=False):
        return self.ask('{}RDG? {}'.format(mode, tag), verbose=verbose)

    def _setpoint1_changed(self):
        self.set_setpoint(self.setpoint1, 1)

    def _setpoint2_changed(self):
        self.set_setpoint(2, self.setpoint2)
# ============= EOF =============================================
