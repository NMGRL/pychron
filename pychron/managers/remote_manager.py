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



import socket

from traits.api import Str, Int, Enum

from pychron.managers.manager import Manager


class RemoteManager(Manager):
    host = Str('localhost')
    port = Int(8080)
    kind = Enum('UDP', 'TCP')

    def ask(self, cmd, port=None):
        r = ''
        conn = self.get_connection(port=port)
        conn.send(cmd)
        try:
            r = conn.recv(4096)
            r = r.strip()
            self.info('-----ask----- {} ==> {}'.format(cmd, r))
        except socket.error, e:
            self.warning(e)

        return r

    def get_connection(self, port=None):
        packet_kind = socket.SOCK_STREAM
        family = socket.AF_INET
        if port is None:
            port = self.port
        addr = (self.host, port)

        if self.kind == 'UDP':
            packet_kind = socket.SOCK_DGRAM

        sock = socket.socket(family, packet_kind)
        sock.settimeout(0.1)
        sock.connect(addr)
        return sock


class RemoteExtractionLineManager(RemoteManager):
    '''
        needs to expose extraction line manager api to an el script
    '''
    def open_valve(self, name, **kw):
        # if the response is OK the valve state actually changed
        # if response is ok valve already in requested state
        resp = self.ask('Open {}'.format(name))
        return 'OK' in resp

    def close_valve(self, name, **kw):
        resp = self.ask('Close {}'.format(name))
        return 'OK' in resp
