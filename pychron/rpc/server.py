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
from traits.api import Any
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable

class RPCServer(Loggable):
    manager = Any

    backend_kind = 'xml'
    port = None

    def bootstrap(self):

        if self.backend_kind == 'pyro':
            from pychron.rpc.backends import PyroBackend
            self._backend = bk = PyroBackend()
        else:
            from pychron.rpc.backends import XMLBackend
            self._backend = bk = XMLBackend()
            bk.port = self.port
        self.info('bootstrap rpc server backend={}'.format(self.backend_kind))
        bk.manager = self.manager
        bk.start_server()


class DummyManager(object):
    def foo(self, a):
        print 'foo', a
        return True

    def moo(self, m, a):
        print 'moo', m, a
        return True

if __name__ == '__main__':
#    from pychron.lasers.laser_managers.fusions_laser_manager import FusionsLaserManager
#    lm = FusionsLaserManager()
    lm = DummyManager()
    s = RPCServer(manager=lm)
    s.bootstrap()

#============= EOF =============================================
