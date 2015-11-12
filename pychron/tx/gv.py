# ===============================================================================
# Copyright 2015 Jake Ross
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
import random

import gevent
from gevent.server import StreamServer


# ============= standard library imports ========================
# ============= local library imports  ==========================

def handle(socket, address):
    data = socket.recv(4096)
    cmd = data.split(' ')[0]
    print socket
    if cmd == 'GetData':
        gevent.sleep(1)
        socket.sendall('Foo')
        # gevent.spawn(getdata, socket, data)
    else:
        msg = 'Random {}'.format(random.random())
        socket.sendall(msg)


def getdata(socket, data):
    s = 0
    # for i in range(int(1e7)):
    # s += 1
    gevent.sleep(1)
    socket.sendall('Foo')


server = StreamServer(('127.0.0.1', 8007), handle)  # creates a new server
server.serve_forever()  # start accepting new connections
# ============= EOF =============================================
