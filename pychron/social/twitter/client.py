# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import
import twitter
from traits.api import Str

from pychron.loggable import Loggable


class TwitterClient(Loggable):
    consumer_key = Str
    consumer_secret = Str
    access_token_key = Str
    access_token_secret = Str

    _api = None

    def test_api(self):
        api = self.connect()
        user = api.VerifyCredentials()
        if user is None:
            connected, err = False, 'Invalid credentials'
        else:
            connected, err = True, ''

        return connected, err

    def connect(self):
        if self._api is None:
            api = twitter.Api(consumer_key=self.consumer_key,
                              consumer_secret=self.consumer_secret,
                              access_token_key=self.access_key,
                              access_token_secret=self.access_secret)
            self._api = api

        return self._api

    def twit(self, msg):
        api = self.connect()
        api.PostUpdate(msg)
# ============= EOF =============================================
