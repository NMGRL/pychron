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
from traits.api import Enum
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice
import re

IDN_RE = re.compile(r'\w{4},\w{8},\w{7}\/\w{7},\d.\d')


class BaseLakeShoreController(CoreDevice):
    units = Enum('C', 'K')

    def load_additional_args(self, config):
        self.set_attribute(config, 'units', 'General', 'units', default='C')
        return True

    def initialize(self, *args, **kw):
        self.communicator.write_terminator = chr(10)  # line feed \n

    def test_connection(self):
        self.tell('*CLS')
        resp = self.ask('*IDN?')
        return bool(IDN_RE.match(resp))

    @get_float
    def read_setpoint(self, output):
        return self.ask('SETP? {}'.format(output))

    def set_setpoint(self, output, v):
        self.tell('SETP {},{}'.format(output, v))

    def read_input_a(self):
        return self._read_input('a', self.units)

    def read_input_b(self):
        return self._read_input('b', self.units)

    @get_float
    def _read_input(self, tag, mode='C'):
        return self.ask('{}RDG? {}'.format(mode, tag))

# ============= EOF =============================================
