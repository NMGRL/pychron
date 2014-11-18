#===============================================================================
# Copyright 2014 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
import SocketServer
import select
import socket
import sys
from threading import Thread


class EmulationServer(object):
    def __init__(self, host, port, emulator):
        self.host = host
        self.port = port
        self.emulator = emulator

    def start(self, join=True):
        if not join:
            t = Thread(target=self.run)
            t.start()
        else:
            self.run()

    def stop(self):
        self._alive = False
        self.server.server_close()

    def run(self, host=None, port=None):
        if host is None:
            host = self.host
        if port is None:
            port = self.port

        if not (port and host):
            return

        print 'serving on {}:{}'.format(host, port)
        server = SocketServer.TCPServer((host, port), self.emulator)
        server.allow_reuse_address = True
        self.server = server

        server.serve_forever()

    def run_link(self, host=None, port=None):
        if host is None:
            host = self.host
        if port is None:
            port = self.port

        if not (port and host):
            return

        self._alive = True
        c = self.emulator
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(5)
        input_ = [server, sys.stdin]

        while self._alive:
            inputready, _outputready, _exceptready = select.select(input_, [], [], 0.05)
            for s in inputready:
                if s == server:
                    # handle the server socket
                    client, _address = server.accept()
                    input_.append(client)

                elif s == sys.stdin:
                    # handle standard input_
                    _junk = sys.stdin.readline()
                    running = 0

                else:
                    # handle all other sockets
                    data = c.handle(s.recv(1024))
                    if data:
                        try:
                            s.send(data)
                        except socket.error:
                            pass
                    else:
                        s.close()
                        input_.remove(s)

#============= EOF =============================================

