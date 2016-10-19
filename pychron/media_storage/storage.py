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
from traits.api import Str

from pychron.loggable import Loggable


class Storage(Loggable):
    def put(self, src, dest):
        raise NotImplementedError


class AuthenticationStorage(Storage):
    username = Str
    password = Str

    def __init__(self, bind=True, *args, **kw):
        super(AuthenticationStorage, self).__init__(*args, **kw)
        if bind:
            self._bind_authentication_preferences()

    def _bind_authentication_preferences(self, prefid=None):
        if prefid is None:
            prefid = 'pychron.media_storage'
        bind_preference(self, 'username', '{}.username'.format(prefid))
        bind_preference(self, 'password', '{}.password'.format(prefid))


class RemoteStorage(AuthenticationStorage):
    host = Str

    def __init__(self, bind=True, *args, **kw):
        super(RemoteStorage, self).__init__(bind=bind, *args, **kw)
        if bind:
            self._bind_remote_preferences()

    def _bind_remote_preferences(self, prefid=None):
        if prefid is None:
            prefid = 'pychron.media_storage'
        bind_preference(self, 'host', '{}.host'.format(prefid))

# ============= EOF =============================================
