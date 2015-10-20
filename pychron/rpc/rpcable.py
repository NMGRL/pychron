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
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
class RPCable(ConfigLoadable):
    rpc_server = None
    def load_rpc_server(self, port):
        self.info('starting rpc server port={}'.format(port))
        from pychron.rpc.server import RPCServer
        self.rpc_server = RPCServer(manager=self,
                                    port=port)
        self.rpc_server.bootstrap()

    def _load_hook(self, config):
        if config.has_section('RPC'):
            rpc_port = self.config_get(config, 'RPC', 'port', cast='int')
            if rpc_port:
                self.load_rpc_server(rpc_port)

# ============= EOF =============================================
