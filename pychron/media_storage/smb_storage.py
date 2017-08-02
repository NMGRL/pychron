# ===============================================================================
# Copyright 2016 ross
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
import os
import socket

from apptools.preferences.preference_binding import bind_preference
from smb.SMBConnection import SMBConnection, OperationFailure
from traits.api import Str

from pychron.media_storage.storage import RemoteStorage


class SMBStorage(RemoteStorage):
    service_name = Str
    url_name = 'SMB'

    def get_base_url(self):
        return 'SMB://{}/{}'.format(self.host, self.service_name)

    def __init__(self, bind=True, *args, **kw):
        super(SMBStorage, self).__init__(bind=bind, *args, **kw)
        if bind:
            bind_preference(self, 'service_name', 'pychron.media_storage.smb_service_name')

    def getlist(self):
        conn = self._get_connection()
        if conn:
            for sf in conn.listPath(self.service_name, '/'):
                print sf.filename

            conn.close()
    # def exists(self, ):
    #     conn = self._get_connection()
    #     if conn:

    def put(self, src, dest):
        conn = self._get_connection()
        if conn:
            # make sure directory available to write to
            if os.path.basename(dest) != dest:
                self._r_mkdir(os.path.dirname(dest), conn)
            if not isinstance(src, (str, unicode)):
                conn.storeFile(self.service_name, dest, src)
            else:
                with open(src, 'r') as rfile:
                    conn.storeFile(self.service_name, dest, rfile)
            conn.close()

    def _r_mkdir(self, dest, conn=None):
        if not os.path.dirname(dest):
            self._mkdir(dest, conn)
        else:
            self._r_mkdir(os.path.dirname(dest))
            self._mkdir(dest, conn)

    def _mkdir(self, dest, conn=None):
        close = False
        if conn is None:
            conn = self._get_connection()
            close = True

        if conn:
            try:
                conn.createDirectory(self.service_name, dest)
            except OperationFailure:
                pass

            if close:
                conn.close()

    def _get_connection(self):
        localname = socket.gethostname()
        remotename = 'agustin'
        conn = SMBConnection(self.username, self.password,
                             localname, remotename)
        self.debug('get connection {}'.format(self.host))
        if conn.connect(self.host):
            return conn
        else:
            print 'failed to connect'


if __name__ == '__main__':
    import logging

    logger = logging.getLogger('SMB')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    s = SMBStorage(bind=False,
                   service_name='argon',
                   username=os.getenv('bureau_username'),
                   password=os.getenv('bureau_password'))
    # s.getlist()
    s.put('/Users/ross/Desktop/argonfiles.txt', 'test/a/argonfiles.txt')
    # s._r_mkdir('test/a')

# ============= EOF =============================================
