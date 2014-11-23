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

# ============= enthought library imports =======================
from traits.api import List
from envisage.plugin import Plugin
from envisage.service_offer import ServiceOffer
# ============= standard library imports ========================
# ============= local library imports  ==========================

SERVICE_OFFERS = 'envisage.service_offers'
TASK_EXTENSIONS = 'envisage.ui.tasks.task_extensions'
TASKS = 'envisage.ui.tasks.tasks'


class BaseTaskPlugin(Plugin):
    actions = List(contributes_to='pychron.actions')

    tasks = List(contributes_to=TASKS)
    service_offers = List(contributes_to=SERVICE_OFFERS)

    my_task_extensions = List(contributes_to=TASK_EXTENSIONS)
    # base_task_extensions = List(contributes_to=TASK_EXTENSIONS)

    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    managers = List(contributes_to='pychron.hardware.managers')

    _tests = None

    def service_offer_factory(self, **kw):
        return ServiceOffer(**kw)

    def check(self):
        return True

    # def system_test(self):
    #     for t in self._tests:
    #         result = self._do_test(t)
    #         self.application.system_tester.add_test_result(result)

    def start(self):
        self.application.system_tester.test_plugin(self)

    # private
    def _get_task_extensions(self):
        return []

    # defaults
    def _preferences_panes_default(self):
        return []

    def _preferences_default(self):
        return []



# ============= EOF =============================================
