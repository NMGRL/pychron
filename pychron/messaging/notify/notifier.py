# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Int, Dict, Bool

import zmq
from threading import Thread, Lock

from pychron.messaging.broadcaster import Broadcaster


class Notifier(Broadcaster):
    _handlers = Dict
    port = Int
    _lock = None

    def setup(self, port):
        if port:
            self._lock = Lock()

            context = zmq.Context()
            self._setup_publish(context, port)

            self._req_sock = context.socket(zmq.REP)
            self._req_sock.bind("tcp://*:{}".format(port + 1))
            #
            t = Thread(name="ping_replier", target=self._handle_request)
            t.setDaemon(1)
            t.start()

    def add_request_handler(self, name, func):
        self._handlers[name] = func

    def close(self):
        with self._lock:
            if self._sock:
                self._sock.setsockopt(zmq.LINGER, 0)
                self._sock.close()
                self._sock = None

            if self._req_sock:
                self._req_sock.setsockopt(zmq.LINGER, 0)
                self._req_sock.close()
                self._req_sock = None

    def send_notification(self, uuid, tag="RunAdded"):
        msg = "{} {}".format(tag, uuid)
        self.info("pushing notification - {}".format(msg))
        self._send(msg)

    def send_console_message(self, msg, tag="ConsoleMessage"):
        msg = "{} {}".format(tag, msg)
        self.info("push console message - {}".format(msg))
        self._send(msg)

    # private
    def _port_changed(self):
        if self.enabled:
            self.setup(self.port)

    def _handle_request(self):
        sock = self._req_sock

        poll = zmq.Poller()
        poll.register(self._req_sock, zmq.POLLIN)

        while sock:
            socks = dict(poll.poll(1000))
            with self._lock:
                try:
                    if socks.get(sock) == zmq.POLLIN:
                        req = sock.recv()
                        if req == "ping":
                            sock.send("echo")
                        elif req in self._handlers:
                            func = self._handlers[req]
                            sock.send(func())
                except zmq.ZMQBaseError:
                    pass

        poll.unregister(self._req_sock)


# ============= EOF =============================================
