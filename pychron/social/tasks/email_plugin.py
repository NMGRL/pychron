#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.social.emailer import Emailer
from pychron.social.tasks.email_preferences import EmailPreferencesPane
from pychron.social.tasks.email_task import EmailTask


class EmailPlugin(BaseTaskPlugin):
    def _service_offer_defaults(self):
        so = self.service_offer_factory(factory=self._email_factory,
                                        protocol=Emailer)

        return [so]

    def _email_factory(self):
        return Emailer()

    def _tasks_default(self):
        t = [TaskFactory(id=self.id,
                         factory=self._task_factory,
                         name='Email', image='email-go'), ]
        return t

    def _task_factory(self):
        return EmailTask()

    def _preferences_panes_default(self):
        return [EmailPreferencesPane]

        #============= EOF =============================================
