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

from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.tasks.furnace_plugin import BaseFurnacePlugin
from pychron.furnace.tasks.ldeo.preferences import LDEOFurnacePreferencesPane, LDEOFurnaceControlPreferencesPane
from pychron.furnace.tasks.ldeo.task import LDEOFurnaceTask


class LDEOFurnacePlugin(BaseFurnacePlugin):
    name = 'LDEOFurnace'
    id = 'pychron.furnace.ldeo.plugin'
    task_name = 'LDEO Furnace'
    klass = ('pychron.furnace.ldeo.furnace_manager', 'LDEOFurnaceManager')
    task_klass = LDEOFurnaceTask

    def _help_tips_default(self):
        return ['LDEOFurnace hardware was designed by Stephen Cox. Firmware and software was designed by Jake '
                'Ross for NMGRL with modifications by Stephen Cox for LDEO']

    def _deactivations_default(self):
        application = self.application

        def func():
            manager = application.get_service(IFurnaceManager)
            if manager:
                for window in application.windows:
                    if 'furnace' in window.active_task.id:
                        break
                else:
                    manager.stop_update()

        return [func]

    def _activations_default(self):
        man = self._get_manager()
        return [man.start_update]

    def test_furnace_api(self):
        man = self._get_manager()
        return man.test_furnace_api()

    def test_furnace_cam(self):
        pass

    def _preferences_panes_default(self):
        return [LDEOFurnacePreferencesPane, LDEOFurnaceControlPreferencesPane]

# ============= EOF =============================================
