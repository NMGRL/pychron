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
from traits.api import HasTraits
from traitsui.api import View, Item
from pychron.lasers.tasks.plugins.laser_plugin import FusionsPlugin
from pychron.lasers.tasks.laser_task import FusionsCO2Task
from pychron.lasers.tasks.laser_preferences import FusionsCO2PreferencesPane
from pychron.lasers.tasks.laser_actions import OpenScannerAction, PowerMapAction, \
    PowerCalibrationAction, TestDegasAction
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group
#============= standard library imports ========================
#============= local library imports  ==========================
class FusionsCO2Plugin(FusionsPlugin):
    id = 'pychron.fusions.co2'
    name = 'fusions_co2'
    klass = ('pychron.lasers.laser_managers.fusions_co2_manager', 'FusionsCO2Manager')
    task_name = 'Fusions CO2'
    accelerator = 'Ctrl+Shift+]'

    def _task_factory(self):
        t = FusionsCO2Task(manager=self._get_manager())
        return t

    def _preferences_panes_default(self):
        return [FusionsCO2PreferencesPane]

    def _my_task_extensions_default(self):
        exts = super(FusionsCO2Plugin, self)._my_task_extensions_default()
        def factory_scan():
            return OpenScannerAction(self._get_manager())
        ext1 = TaskExtension(task_id='pychron.fusions.co2',
                             actions=[
#                                       SchemaAddition(id='fusions_co2_group',
#                                              factory=lambda: MenuSchema(id='FusionsCO2',
#                                                                         name='Fusions CO2'
#                                                                    ),
#                                              path='MenuBar/Extraction'
#                                              ),
                                      SchemaAddition(id='calibration',
                                                   factory=lambda: Group(
                                                                         PowerMapAction(),
                                                                         PowerCalibrationAction(),
                                                                         ),
                                                   path='MenuBar/Laser'
                                                   ),
                                      SchemaAddition(
                                                   factory=TestDegasAction,
                                                   path='MenuBar/Laser'
#                                                    path='MenuBar/Extraction'
                                                   )
                                     ]
                              )

        return exts + [ext1]
#============= EOF =============================================
