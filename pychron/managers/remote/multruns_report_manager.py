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
#============= local library imports  ==========================
from pychron.managers.multruns_report_manager import MultrunsReportManager
from pychron.has_communicator import HasCommunicator
from pychron.rpc.query import rpc_query


class RemoteMultrunsReportManager(MultrunsReportManager, HasCommunicator):

    @rpc_query
    def get_current_rid(self, *args, **kw):
        print 'get rid'
        pass

    def load(self):
        config = dict(port=self.rpc_port,
                      backend='xml',
                      host=self.rpc_host,
                      )
        self._load_communicator(config, 'RPC')
        return True
#============= EOF =============================================
