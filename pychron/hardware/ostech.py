# ===============================================================================
# Copyright 2020 ross
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
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.data_helper import make_bitarray


class OsTechLaserController(CoreDevice):
    def initialize(self, *args, **kw):
        self.communicator.read_terminator = '\r'
        self.communicator.echos_command = True
        # switch to reduced mode
        resp = bool(self.ask('GMS32768', verbose=True))

        if resp:
            self.check_interlocks()

        return resp
        # return True

    def check_interlocks(self):
        resp = self.ask('GS', verbose=True)
        self.debug('interlocks {}'.format(resp))
        interlocks = int(resp)
        bits = make_bitarray(interlocks)[::-1]
        self.debug('{}'.format(bits))
        bitmap = [(0x0001, 'Interlock', False),
                  (0x0004, 'driver supply', False),
                  (0x0008, 'driver temperature', False),
                  (0x0010, 'LTLU', True),
                  (0x0020, 'LTLL', True),
                  (0x0040, 'CTLU', True),
                  (0x0080, 'CTLL', True),
                  (0x0400, 'LT sensor', False),
                  (0x0800, 'CT sensor', False),
                  (0x2000, 'LTM', True),
                  #(0x4000, 'LC', False),
                  #(0x8000, 'LC error', False)
                  ]

        failures = []
        for t, il, inv in bitmap:
            ok = bool(t & interlocks)
            if inv:
                ok = not ok

            self.info('Check {} {}'.format(il, 'OK' if ok else 'Not OK'))
            if not ok:
                self.warning('Status failure= {}'.format(il))
                failures.append(il)

        return failures

    def enable(self, *args, **kw):
        if not self.check_interlocks():
            return bool(self.ask('LR', verbose=True))

    def disable(self, *args, **kw):
        return bool(self.ask('LS'))

# ============= EOF =============================================
