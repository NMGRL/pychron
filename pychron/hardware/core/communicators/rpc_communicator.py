# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# import xmlrpclib
# import hmac
# import Pyro4 as pyro
# pyro.configuration.HMAC_KEY = bytes(hmac.new('pychronjjj.rpc.hmac').digest())

# ============= local library imports  ==========================
from pychron.hardware.core.communicators.communicator import Communicator

# return to xml-rpc ?

class RpcCommunicator(Communicator):
    '''
    '''
    test_func = None
    def load(self, config, path):
        '''
        '''
        self._backend_load_hook(config)
        return True

    def initialize(self, **kw):
        if self.test_func is None:
            self.info('not testing rpc communicator {}'.format(self.name))
            self.simulation = False
            return True

        self.info('testing rpc communicator - {} test_func={}'.format(self.name,
                                                                      self.test_func
                                                                      ))
        try:
            getattr(self.handle, self.test_func)()
            self.simulation = False
            return True
        except Exception, err:
            self.warning(err)

    def config_get(self, config, section, option, **kw):
        if isinstance(config, dict):
            try:
                return config[option]
            except KeyError:
                pass
        else:
            return super(RpcCommunicator, self).config_get(config, section, option, **kw)

    def _backend_load_hook(self, config):
        backend = self.config_get(config, 'Communications', 'backend', optional=True)
        self.set_attribute(config, 'test_func', 'Communications', 'test_func')
        if backend == 'pyro':
            from pychron.rpc.backends import PyroBackend
            bk = PyroBackend()
            bk.name = self.config_get(config, 'Communications', 'name')
        else:
            from pychron.rpc.backends import XMLBackend
            bk = XMLBackend()
            bk.port = self.config_get(config, 'Communications', 'port')
            bk.host = self.config_get(config, 'Communications', 'host')

        self._rpc_backend = bk

    def _get_handle(self):
        return self._rpc_backend.handle

    handle = property(fget=_get_handle)
# ============= EOF =============================================
