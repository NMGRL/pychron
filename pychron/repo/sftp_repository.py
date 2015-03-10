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

from traits.api import Property

# ============= standard library imports ========================
import os
import paramiko
import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

# ============= local library imports  ==========================
from pychron.repo.repository import RemoteRepository


class SFTPRepository(RemoteRepository):
    client = Property(depends_on='host, username, password')
    _client = None
    _server_root = None

    enabled = False
    def _get_client(self):
        if self._client is not None:
            return self._client

        t = paramiko.Transport((self.host, 22))
        t.connect(username=self.username,
                  password=self.password)
        self.enabled=True
        sftp = paramiko.SFTPClient.from_transport(t)
        self._client = sftp
        return self._client

    def connect(self):
        return self.client

    def add_file(self, p):

        def cb(clt):
            bp = os.path.basename(p)
            self.info('adding {} to {}'.format(bp, clt.getcwd()))
            clt.put(p, bp)

        self._execute(cb)

    def isfile(self, n):
        def cb(clt):
            return n in clt.listdir()

        self._execute(cb)

    def _execute(self, cb):
        client = self.client
        if self.enabled:
            if self._server_root is None:
                self._server_root = client.getcwd()

            if not client.getcwd() == os.path.join(self._server_root, self.root):
                client.chdir(self.root)
            try:
                return cb(client)
            except paramiko.BadAuthenticationType:
                self.enabled=False

    #        return os.path.isfile(self.get_file_path(n))

    def retrieveFile(self, n, out):
        # print n, out
        def cb(clt):
            clt.get(n, out)

        self._execute(cb)

# ============= EOF =============================================



