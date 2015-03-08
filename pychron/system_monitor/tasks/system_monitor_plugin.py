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
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import List
# ============= standard library imports ========================
# ============= local library imports  ==========================

#from pychron.processing.tasks.browser.browser_task import BrowserTask
from pychron.dashboard.tasks.client.preferences import DashboardClientPreferencesPane
from pychron.file_defaults import DISPLAY_FORMATTING_DEFAULTS
from pychron.paths import paths
from pychron.processing.tasks.processing_plugin import ProcessingPlugin
from pychron.system_monitor.tasks.preferences import SystemMonitorPreferencesPane, ConsolePreferencesPane
from pychron.system_monitor.tasks.system_monitor_task import SystemMonitorTask


class SystemMonitorPlugin(ProcessingPlugin):

    def start(self):
        pass

    def _task_factory(self):
        return SystemMonitorTask(manager=self._processor_factory())

    def _task_extensions_default(self):
        return []

    def _tasks_default(self):
        return [TaskFactory(name='System Monitor',
                            id='pychron.system_monitor',
                            accelerator='Ctrl+Shift+V',
                            factory=self._task_factory)]

    def _preferences_panes_default(self):
        return [SystemMonitorPreferencesPane,
                ConsolePreferencesPane,
                DashboardClientPreferencesPane]

    # def _file_defaults_default(self):
    #     return []
        # ============= EOF =============================================
