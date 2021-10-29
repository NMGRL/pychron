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
from pymodbus.client.sync import ModbusTcpClient

from pychron.hardware.core.communicators.communicator import Communicator
from pymodbus.constants import Defaults


class ModbustcpCommunicator(Communicator):
    host = None
    timeout = None

    def load(self, config, path):
        self.host = self.config_get(config, "Communications", "host")
        self.timeout = self.config_get(
            config, "Communications", "timeout", cast="int", default=Defaults.Timeout
        )
        return super(ModbustcpCommunicator, self).load(config, path)

    def open(self, *args, **kw):
        a = self.host
        self.handle = ModbusTcpClient(a, timeout=self.timeout)
        return True

    def initialize(self, *args, **kw):
        return self.handle.connect()

    def __getattr__(self, item):
        return getattr(self.handle, item)


# ============= EOF =============================================
