# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import CInt, Str, Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.has_communicator import HasCommunicator
from pychron.loggable import Loggable


class RemoteDeviceMixin(Loggable, HasCommunicator):
    connected = False

    kind = Str
    message_frame = Str
    use_end = Bool
    timeout = CInt
    write_terminator = chr(10)
    read_terminator = ""

    def open(self):
        return self.setup_communicator()

    def opened(self):
        pass

    def shutdown(self):
        self.close_communicator()

    def setup_communicator(self):
        raise NotImplementedError

    def _ask(self, *args, **kw):
        if not self.communicator:
            self.setup_communicator()

        if self.communicator:
            return self.communicator.ask(*args, **kw)


class SerialDeviceMixin(RemoteDeviceMixin):
    port = Str
    baudrate = CInt
    parity = Str
    stopbits = Str
    read_delay = CInt

    def setup_communicator(self):
        ec = self.build_communicator("serial")
        if ec is None:
            return
        ec.port = self.port
        ec.baudrate = self.baudrate
        ec.read_delay = self.read_delay
        ec.set_parity(self.parity)
        ec.set_stopbits(self.stopbits)
        return ec.open(timeout=self.timeout)


class EthernetDeviceMixin(RemoteDeviceMixin):
    port = CInt
    host = Str
    timeout = CInt

    def setup_communicator(
        self, write_terminator=None, read_terminator=None, force=False
    ):
        if write_terminator is None:
            write_terminator = self.write_terminator

        if read_terminator is None:
            read_terminator = self.read_terminator

        ret = True
        if force or self.communicator is None:
            ec = self.build_communicator("ethernet")
            if ec is None:
                return
            ec.host = self.host
            ec.port = self.port
            ec.kind = self.kind
            ec.use_end = self.use_end
            ec.message_frame = self.message_frame
            ec.write_terminator = write_terminator
            ec.read_terminator = read_terminator
            ec.timeout = self.timeout
            ret = ec.open()
            if self.communicator:
                self.communicator.report()

        return ret


# ============= EOF =============================================
