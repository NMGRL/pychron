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
from traits.api import HasTraits, Button, CInt, Str
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator

from pychron.loggable import Loggable


class PychronDevice(Loggable):
    communicator = None
    connected = False
    port = CInt
    host = Str
    message_frame = Str

    def setup_communicator(self):
        host = self.host
        port = self.port
        self.communicator = ec = EthernetCommunicator(host=host,
                                                      port=port,
                                                      message_frame=self.message_frame)

        r = ec.open()
        if r:
            r = self.opened()
            self.connected = bool(r)

        return r

    def open(self):
        return self.setup_communicator()
        # host = self.host
        # port = self.port
        #
        # self.communicator = ec = EthernetCommunicator(host=host,
        #                                               port=port)
        # r = ec.open()
        # if r:
        #     self.connected = True
        #     self.opened()
        #
        # return r

    def opened(self):
        pass

    def shutdown(self):
        if self.communicator:
            self.communicator.close()

    def _ask(self, *args, **kw):
        if not self.communicator:
            self.setup_communicator()

        if self.communicator:
            return self.communicator.ask(*args, **kw)

# ============= EOF =============================================



