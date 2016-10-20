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

import os
import shutil
import socket

from apptools.preferences.preference_binding import bind_preference
from traits.api import Str

from pychron.media_storage.storage import Storage
from pychron.paths import paths


class FileStorage(Storage):
    root = Str
    url_name = 'file'

    def __init__(self, *args, **kw):
        super(FileStorage, self).__init__(*args, **kw)
        bind_preference(self, 'root', 'pychron.media_storage.root')

    def get_host(self):
        return socket.getfqdn()

    def put(self, src, dest):
        root = self.root
        if root is None:
            root = paths.media_storage_dir

        dest = os.path.join(root, dest)
        shutil.copyfile(src, dest)
        return 'file:{}'.format(dest)

# ============= EOF =============================================
