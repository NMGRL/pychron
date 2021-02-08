# ===============================================================================
# Copyright 2021 ross
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
from pychron.hardware.core.communicators.serial_communicator import SerialCommunicator
from pywatlow.watlow import Watlow


class WatlowStandardBusCommunicator(SerialCommunicator):
    def open(self, **kw):
        self.handle = Watlow(port=self.port,
                             address=self.address)
        return True

    def read(self, param, response_type='int', *args, **kw):
        rt = float
        if response_type == 'int':
            rt = int

        resp = self.handle.readParam(param, rt)
        if resp['error'] is None:
            return resp['data']

    def write(self, param, value, *args, **kw):
        self.handle.writeParam(param, value, type(value))
# ============= EOF =============================================
