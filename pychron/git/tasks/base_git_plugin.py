# ===============================================================================
# Copyright 2016 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.git.hosts import IGitHost


class BaseGitPlugin(BaseTaskPlugin):
    service_klass = None

    def start(self):
        p = self.application.preferences
        usr = p.get('pychron.github.user')
        pwd = p.get('pychron.github.password')
        tok = p.get('pychron.github.token')
        self.debug('user={}, pwd={}, token={}'.format(usr, pwd, tok))
        if not tok and not (usr and pwd):
            self.information_dialog('Please set user name and password or token in preferences')

    def test_api(self):
        service = self.application.get_service(IGitHost)
        return service.test_api()

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=IGitHost,
                                        factory=self._factory)

        return [so, ]

    def _factory(self):
        c = self.service_klass()
        c.bind_preferences()
        return c

# ============= EOF =============================================
