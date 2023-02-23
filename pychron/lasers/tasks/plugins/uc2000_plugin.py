# ===============================================================================
# Copyright 2023 ross
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
from pychron.lasers.tasks.laser_preferences import TAPDiodePreferencesPane, UC2000CO2PreferencesPane
from pychron.lasers.tasks.laser_task import TAPDiodeTask, UC2000CO2Task
from pychron.lasers.tasks.plugins.laser_plugin import BaseLaserPlugin

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pychron_constants import UC2000_CO2


class UC2000CO2Plugin(BaseLaserPlugin):
    id = "pychron.uc2000.co2"
    name = UC2000_CO2.replace(" ", "")

    klass = ("pychron.lasers.laser_managers.uc2000_laser_manager", "UC2000CO2Manager")
    task_name = UC2000_CO2
    accelerator = "Ctrl+Shift+["

    # def _task_extensions_default(self):
    #
    #     exts = super(UC2000LaserPlugin, self)._task_extensions_default()
    #
    #     ext1 = TaskExtension(
    #         task_id='pychron.fusions.diode',
    #         actions=[SchemaAddition(id='calibration',
    #                                 factory=lambda: Group(
    #                                     # PowerMapAction(),
    #                                     # PowerCalibrationAction(),
    #                                     # PyrometerCalibrationAction(),
    #                                     PIDTuningAction()),
    #                                 path='MenuBar/Laser'),
    #                  # SchemaAddition(
    #                  #     factory=TestDegasAction,
    #                  #     path='MenuBar/Laser'),
    #                  # SchemaAddition(
    #                  #     factory=lambda: ExecutePatternAction(self._get_manager()),
    #                  #     path='MenuBar/Laser')
    #                  ])
    #
    #     return exts + [ext1]

    def _preferences_panes_default(self):
        return [UC2000CO2PreferencesPane]

    def _task_factory(self):
        t = UC2000CO2Task(manager=self._get_manager(), application=self.application)
        return t


# ============= EOF =============================================
