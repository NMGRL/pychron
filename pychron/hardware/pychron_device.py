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
from pychron.loggable import Loggable


class RemoteDeviceMixin(Loggable):
    communicator = None
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
        if self.communicator:
            self.communicator.close()

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
        from pychron.hardware.core.communicators.serial_communicator import (
            SerialCommunicator,
        )

        self.communicator = ec = SerialCommunicator(
            port=self.port,
            baudrate=self.baudrate,
            read_delay=self.read_delay,
        )
        ec.set_parity(self.parity)
        ec.set_stopbits(self.stopbits)
        return ec.open(timeout=self.timeout)


class EthernetDeviceMixin(RemoteDeviceMixin):
    port = CInt
    host = Str
    timeout = CInt

    def setup_communicator(self, write_terminator=None, read_terminator=None):
        from pychron.hardware.core.communicators.ethernet_communicator import (
            EthernetCommunicator,
        )

        if write_terminator is None:
            write_terminator = self.write_terminator

        if read_terminator is None:
            read_terminator = self.read_terminator

        self.communicator = ec = EthernetCommunicator(
            host=self.host,
            port=self.port,
            kind=self.kind,
            use_end=self.use_end,
            message_frame=self.message_frame,
            write_terminator=write_terminator,
            read_terminator=read_terminator,
            timeout=self.timeout,
        )

        return ec.open()


# ============= EOF =============================================
