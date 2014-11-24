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
from envisage.ui.tasks.task_extension import TaskExtension
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.lasers.tasks.plugins.laser_plugin import FusionsPlugin
from pychron.lasers.tasks.laser_preferences import FusionsUVPreferencesPane


class FusionsUVPlugin(FusionsPlugin):
    id = 'pychron.fusions.uv'
    name = 'FusionsUV'
    klass = ('pychron.lasers.laser_managers.fusions_uv_manager', 'FusionsUVManager')
    task_name = 'Fusions UV'
    accelerator = 'Ctrl+Shift+\\'

    def _my_task_extensions_default(self):
        exts = super(FusionsUVPlugin, self)._my_task_extensions_default()

        ext1 = TaskExtension(task_id='pychron.fusions.uv')

        return exts + [ext1]

    def _preferences_panes_default(self):
        return [FusionsUVPreferencesPane]

    def _task_factory(self):
        from pychron.lasers.tasks.laser_task import FusionsUVTask
        t = FusionsUVTask(manager=self._get_manager())
        return t

# ============= EOF =============================================
