# ===============================================================================
# Copyright 2023 Jake Ross
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
from pychron.furnace.tasks.reston.preferences import RestonFurnacePreferencesPane
from pychron.furnace.tasks.reston.task import RestonFurnaceTask


class RestonFurnacePlugin(BaseFurnacePlugin):
    name = "RestonFurnace"
    id = "pychron.furnace.reston.plugin"

    klass = ("pychron.furnace.reston.furnace_manager", "RestonFurnaceManager")
    task_klass = RestonFurnaceTask

    def _deactivations_default(self):
        application = self.application

        def func():
            manager = application.get_service(IFurnaceManager)
            if manager:
                for window in application.windows:
                    if "furnace" in window.active_task.id:
                        break
                else:
                    manager.stop_update()

        return [func]

    def _activations_default(self):
        man = self._get_manager()
        return [man.start_update]

    def _panes_default(self):
        def f():
            from pychron.furnace.tasks.reston.panes import ExperimentFurnacePane

            manager = self._get_manager()
            fpane = ExperimentFurnacePane(model=manager)
            return fpane

        return [f]

    def _preferences_panes_default(self):
        return [RestonFurnacePreferencesPane]


# ============= EOF =============================================
