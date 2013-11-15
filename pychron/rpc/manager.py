#===============================================================================
# Copyright 2012 Jake Ross
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
import xmlrpclib
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.rpc.server import RPCServer

class RpcServer(Manager):
    def load(self):
        self.server = RPCServer(manager=self.manager)
        return True

    def initialize(self):
        self.server.bootstrap()

class RpcClient(Manager):

    def get_handle(self):
        host = 'localhost'
        port = 8000
        handle = xmlrpclib.ServerProxy('http://{}:{}'.format(host, port))
        return handle

class DummyManager(object):
    def foo(self, a):
        print 'foo', a
        return True

    def moo(self, m, a):
        print 'moo', m, a
        return True

    def test_command(self):
        return 'ttttt'

if __name__ == '__main__':
    s = RpcServer(manager=DummyManager())

    s.bootstrap()
    s.configure_traits()
#============= EOF =============================================
