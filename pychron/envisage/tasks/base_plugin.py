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
from envisage.plugin import Plugin
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class BasePlugin(Plugin, Loggable):
    def _set_preference_defaults(self, defaults, prefid):
        """

        :param defaults: list(tuple) [(str, object),]
        :param prefid: str preference_path e.g pychron.update
        :return:
        """
        change = False
        prefs = self.application.preferences
        self.debug('setting default preferences for {} {}'.format(self.name, self.id))
        for k, d in defaults:
            if k not in prefs.keys(prefid):
                self.debug('Setting default preference {}={}'.format(k, d))
                prefs.set('{}.{}'.format(prefid, k), d)
                change = True

        if change:
            prefs.flush()
        else:
            self.debug('defaults already set')

# ============= EOF =============================================



