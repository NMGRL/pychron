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

from apptools.preferences.preference_binding import bind_preference
from traits.api import Enum

from pychron.loggable import Loggable
from pychron.media_storage import BACKENDS
from pychron.media_storage.file_storage import FileStorage
from pychron.media_storage.ftp_storage import SFTPStorage, FTPStorage
from pychron.media_storage.http_storage import HTTPStorage
from pychron.media_storage.smb_storage import SMBStorage

BACKEND_DICT = {'Local': FileStorage, 'SFTP': SFTPStorage, 'FTP': FTPStorage,
                'SMB': SMBStorage, 'HTTP': HTTPStorage}


class MediaStorageManager(Loggable):
    backend_kind = Enum(BACKENDS)

    def __init__(self, *args, **kw):
        super(MediaStorageManager, self).__init__(*args, **kw)

        prefid = 'pychron.media_storage'
        bind_preference(self, 'backend_kind', '{}.backend_kind'.format(prefid))
        self._backend_kind_changed(self.backend_kind)

    def _backend_kind_changed(self, new):
        if new:
            klass = BACKEND_DICT[new]
            self.storage = klass()

    def get_host(self):
        return self.storage.host

    def get_base_url(self):
        return self.storage.get_base_url()

    def put(self, local_path, remote_path):
        self.storage.put(local_path, remote_path)
        return '{}:{}'.format(self.get_base_url(), remote_path)

    def get(self, remote_path, dest):
        return self.storage.get(remote_path, dest)

    def exists(self, remote_path):
        self.storage.exists(remote_path)

    def add_image_to_db(self, url, analysis_uuid):
        pass

# ============= EOF =============================================
