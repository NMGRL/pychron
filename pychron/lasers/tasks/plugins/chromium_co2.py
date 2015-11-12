# ===============================================================================
# Copyright 2013 Jake Ross
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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.lasers.tasks.plugins.laser_plugin import BaseLaserPlugin
from pychron.lasers.tasks.laser_preferences import FusionsCO2PreferencesPane



class ChromiumCO2Plugin(BaseLaserPlugin):
    id = 'pychron.chromium.co2'
    name = 'ChromiumCO2'
    klass = ('pychron.lasers.laser_managers.chromium_laser_manager', 'ChromiumCO2Manager')
    task_name = 'Chromium CO2'
    accelerator = 'Ctrl+Shift+]'

    def test_communication(self):
        man = self._get_manager()
        c = man.test_connection()
        return 'Passed' if c else 'Failed'

    def _task_factory(self):
        from pychron.lasers.tasks.laser_task import ChromiumCO2Task

        t = ChromiumCO2Task(manager=self._get_manager())
        return t

    def _tasks_default(self):
        return [TaskFactory(id=self.id,
                            task_group='hardware',
                            factory=self._task_factory,
                            name=self.task_name,
                            image='laser',
                            accelerator=self.accelerator)]

# ============= EOF =============================================
