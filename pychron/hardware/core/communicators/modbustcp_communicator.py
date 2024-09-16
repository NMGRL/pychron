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
import logging

from pymodbus.client import ModbusTcpClient

from pychron.hardware.core.communicators.communicator import Communicator


class ModbustcpCommunicator(Communicator):
    host = None
    timeout = None
    port = 502
    byteorder = "big"
    wordorder = "little"

    def load(self, config, path):

        logger = logging.getLogger("pymodbus.logging")
        logger.setLevel(logging.ERROR)
        self.host = self.config_get(config, "Communications", "host")
        self.port = self.config_get(
            config, "Communications", "port", cast="int", default=502
        )
        self.byteorder = self.config_get(
            config, "Communications", "byteorder", default="big"
        )
        self.wordorder = self.config_get(
            config, "Communications", "wordorder", default="little"
        )
        self.timeout = self.config_get(
            config, "Communications", "timeout", cast="int", default=2
        )
        return super(ModbustcpCommunicator, self).load(config, path)

    def open(self, *args, **kw):
        a = self.host
        self.handle = ModbusTcpClient(a, timeout=self.timeout, port=self.port)
        return True

    def initialize(self, *args, **kw):
        return self.handle.connect()

    def __getattr__(self, item):
        return getattr(self.handle, item)


# ============= EOF =============================================
