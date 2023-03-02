# ===============================================================================
# Copyright 2023 ross
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
import socket
import telnetlib

from pychron.hardware.core.communicators.communicator import (
    Communicator,
    process_response,
)
from pychron.regex import IPREGEX


class TelnetCommunicator(Communicator):
    host = None
    port = None
    timeout = 1.0

    _tn = None

    def load(self, config, path):
        super(TelnetCommunicator, self).load(config, path)
        self.timeout = self.config_get(
            config,
            "Communications",
            "timeout",
            cast="float",
            optional=True,
            default=1.0,
        )

        self.host = self.config_get(config, "Communications", "host")

        if self.host != "localhost" and not IPREGEX.match(self.host):
            try:
                result = socket.getaddrinfo(self.host, 0, 0, 0, 0)
                if result:
                    for family, kind, a, b, host in result:
                        if family == socket.AF_INET and kind == socket.SOCK_STREAM:
                            self.host = host[0]
            except socket.gaierror:
                self.debug_exception()

        self.port = self.config_get(config, "Communications", "port", cast="int")
        return True

    def open(self, *args, **kw):
        self._tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        return True

    def ask(self, cmd, verbose=False, *args, **kw):
        cmd = f"{cmd}{self.write_terminator}"

        self._tn.write(cmd.encode("utf8"))

        if self.read_terminator:
            r = self._tn.read_until(self.read_terminator, timeout=self.timeout)
        else:
            r = self._tn.read_all()

        if r is not None:
            r = r.decode("ascii")
            re = process_response(r)

        if verbose:
            self.log_response(cmd, re)

        return r


# ============= EOF =============================================
