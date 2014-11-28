# ===============================================================================
# Copyright 2013 Jake Ross
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
import urllib
import urllib2

from traits.api import Str, Password, Button, on_trait_change, Bool

from pychron.loggable import Loggable
#============= standard library imports ========================
#============= local library imports  ==========================
class HTTPRepository(Loggable):
    username = Str
    password = Password
    url = Str
    upload_button = Button('upload')
    enabled = Bool(False)

    def _upload_button_fired(self):
        self.upload()

    def upload(self):
        pass

    def post(self, path, body):
        if isinstance(body, dict):
            body = urllib.urlencode(body)

        host = self.url
        while host.endswith('/'):
            host = host[:-1]

        while path.startswith('/'):
            path = path[1:]

        url = '{}/{}'.format(host, path)
        try:
            f = urllib2.urlopen(url, body)
        except urllib2.URLError:
            self.warning_dialog('Connection refused to {}'.format(url))
            return

        resp = f.read()
        self.debug('POST response len={}, {}'.format(len(resp), resp))
        self._handle_post(resp)

    def _handle_post(self, resp):
        pass

    def _new_form(self, authenication=True):
        form = dict()
        if authenication:
            form['username'] = self.username
            form['password'] = self.password
        return form

# ===============================================================================
# handlers
# ===============================================================================
    @on_trait_change('username, password')
    def _update_enabled(self):
        self.enabled = all([getattr(self, a)
                                 for a in ('username', 'password')])

# ============= EOF =============================================
