# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.hardware.core.communicators.communicator import Communicator

class MDriveCommunicator(Communicator):
    def open(self):
        self.handle = serial.Serial(self.address, baudrate=self.baudrate, timeout=1)
        
    def tell(self, cmd):
        self.handle.write(self._format_command(cmd))
        return self._read_command_ok()
        
    def ask(self, cmd, multiline=False):
        self.handle.write(self._format_command(cmd))
        return self._read_response(multiline)

    def _read_command_ok(self):
        resp = self.handle.read(2)
        return resp==self.terminator

    def _read_response(self, multiline):
  	terminator = self.terminator
	handle = self.handle

        if self._read_command_ok():
            x=''
            while 1:
                r = handle.read()
                x+=r
                if x.endswith(terminator) and not x==terminator:
                    if multiline:
                        r = handle.read()
                        if not r:
                            break
                        else:
                            x+=r
                    else:
                        break
            return x.strip()
        
    def _format_command(self, cmd):
        return '{}{}'.format(cmd, self.terminator)

# ============= EOF ====================================
