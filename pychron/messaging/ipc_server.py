# ===============================================================================
# Copyright 2011 Jake Ross
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
from __future__ import absolute_import
import socket
from six.moves.socketserver import ThreadingUnixStreamServer

# from threading import Thread
# import select
# ============= local library imports  ==========================
from .messaging_server import MessagingServer
from pychron.messaging.handlers.ipc_handler import IPCHandler


class IPCServer(ThreadingUnixStreamServer, MessagingServer):
    """ """

    def __init__(self, parent, processor_type, datasize, *args, **kw):
        """ """

        self.parent = parent
        self.repeater = parent.repeater

        self.datasize = datasize
        self.processor_type = processor_type

        self.connected = True

        try:
            args += (IPCHandler,)
            super(IPCServer, self).__init__(*args, **kw)
        except socket.error as e:
            self.warning(e)
            self.connected = False


# ============= EOF ====================================
