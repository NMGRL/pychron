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

from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Enum, Str, Password
from traitsui.api import View, Item, VGroup
from traitsui.editors import DirectoryEditor

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.media_storage import BACKENDS
from pychron.paths import paths


class MediaStoragePreferences(BasePreferencesHelper):
    preferences_path = 'pychron.media_storage'
    backend_kind = Enum(BACKENDS)

    root = Str

    host = Str
    username = Str
    password = Password
    smb_service_name = Str


class MediaStoragePreferencesPane(PreferencesPane):
    model_factory = MediaStoragePreferences
    category = 'MediaStorage'

    def traits_view(self):
        local_grp = VGroup(Item('root', editor=DirectoryEditor(root_path=paths.media_storage_dir)),
                           visible_when='backend_kind=="Local"')
        remote_grp = VGroup(Item('host', label='Host'),
                            Item('username', label='Username'),
                            Item('password', label='Password'),
                            visible_when='backend_kind in ("SFTP", "FTP", "SMB")')

        smb_grp = VGroup(Item('smb_service_name', label='SMB Root Folder'),
                         visible_when='backend_kind=="SMB"')
        v = View(VGroup(Item('backend_kind',
                             label='Backend'),
                        local_grp,
                        remote_grp,
                        smb_grp))
        return v

# ============= EOF =============================================
