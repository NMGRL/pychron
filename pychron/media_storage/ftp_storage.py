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
from ftplib import FTP

import paramiko

from pychron.media_storage.storage import RemoteStorage


class FTPStorage(RemoteStorage):

    def put(self, src, dest):
        client = self._get_client()
        self._put(client, src, dest)
        self._close_client(client)

    def _close_client(self, client):
        client.quit()

    def _get_client(self):
        client = FTP(self.host)
        client.login(self.username, self.password)

        return client

    def _put(self, client, src, dest):
        head, ext = os.path.splitext(src)
        if ext in ('.jpg', '.png'):
            with open(src, 'rb') as rfile:
                client.storbinary('STOR {}'.format(dest), rfile, 1024)
        else:
            with open(src, 'r') as rfile:
                client.storlines('STOR {}'.format(dest), rfile)


class SFTPStorage(FTPStorage):
    def _get_client(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.host, username=self.username, password=self.password, timeout=2)
        except (socket.timeout, paramiko.AuthenticationException):
            self.warning_dialog('Could not connect to server')
            return

        return ssh.open_sftp()

    def _close_client(self, client):
        client.close()

    def _put(self, client, src, dest):
        client.put(src, dest)

# ============= EOF =============================================
