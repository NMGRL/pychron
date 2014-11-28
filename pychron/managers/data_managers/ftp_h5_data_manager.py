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

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.managers.data_managers.h5_data_manager import H5DataManager
from pychron.repo.repository import SFTPRepository


class FTPH5DataManager(H5DataManager):

    def connect(self, host, usr, pwd, remote):
        self.repository = SFTPRepository(host=host,
                                         username=usr,
                                         password=pwd,
                                         root=remote)

#    def open_data(self, path, **kw):
#        if self.repository:
#            out = os.path.join(self.workspace_root, path)
#            path = os.path.join(self.repository.root, path)
#            if not os.path.isfile(out):
#                self.info('copying {} to repository {}'.format(path, os.path.dirname(out)))
#                self.repository.retrieveFile(path, out)
#            path = out
# ##        out = os.path.join(self.workspace_root, p)
# ##        self.repository.retrieveFile(p, out)
#        return super(FTPH5DataManager, self).open_data(path, **kw)

    def isfile(self, path):
        return self.repository.isfile(path)

# ============= EOF =============================================
