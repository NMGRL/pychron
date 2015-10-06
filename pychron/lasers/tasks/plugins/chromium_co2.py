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
from pyface.tasks.action.schema_addition import SchemaAddition

from pyface.action.group import Group

from pychron.lasers.tasks.plugins.laser_plugin import FusionsPlugin
from pychron.lasers.tasks.laser_preferences import FusionsCO2PreferencesPane
from pychron.lasers.tasks.laser_actions import PowerMapAction, \
    PowerCalibrationAction, ExecutePatternAction





# ============= standard library imports ========================
# ============= local library imports  ==========================


class ChromiumLaserPlugin(FusionsPlugin):
    id = 'pychron.chromium.co2'
    name = 'ChromiumLaser'
    klass = ('pychron.lasers.laser_managers.chromium_laser_manager', 'ChromiumLaserManager')
    task_name = 'Chromium CO2'
    accelerator = 'Ctrl+Shift+]'

    def _task_factory(self):
        from pychron.lasers.tasks.laser_task import ChromiumCO2Task

        t = ChromiumCO2Task(manager=self._get_manager())
        return t

    def _preferences_panes_default(self):
        return [FusionsCO2PreferencesPane]

    def _task_extensions_default(self):
        exts = super(ChromiumLaserPlugin, self)._task_extensions_default()

        ext1 = TaskExtension(task_id='pychron.chromium.co2',
                             actions=[SchemaAddition(id='calibration',
                                                     factory=lambda: Group(PowerMapAction(),
                                                                           PowerCalibrationAction()),
                                                     path='MenuBar/Laser'),
                                      SchemaAddition(
                                          factory=lambda: ExecutePatternAction(self._get_manager()),
                                          path='MenuBar/Laser'),
                                      # SchemaAddition(factory=TestDegasAction,
                                      #                path='MenuBar/Laser')
                                      ])

        return exts + [ext1]

# ============= EOF =============================================
