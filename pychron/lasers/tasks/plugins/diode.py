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
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group

from pychron.lasers.tasks.plugins.laser_plugin import FusionsPlugin
from pychron.lasers.tasks.laser_actions import OpenScannerAction, \
    OpenAutoTunerAction, PowerMapAction, PowerCalibrationAction, TestDegasAction, PyrometerCalibrationAction
from pychron.lasers.tasks.laser_preferences import FusionsDiodePreferencesPane
from pychron.lasers.tasks.laser_task import FusionsDiodeTask

#============= standard library imports ========================
#============= local library imports  ==========================
class FusionsDiodePlugin(FusionsPlugin):
    id = 'pychron.fusions.diode'
    name = 'fusions_diode'
    klass = ('pychron.lasers.laser_managers.fusions_diode_manager', 'FusionsDiodeManager')
    task_name = 'Fusions Diode'
    accelerator = 'Ctrl+Shift+['

    def _my_task_extensions_default(self):
        def factory_scan():
            return OpenScannerAction(self._get_manager())

        def factory_tune():
            return OpenAutoTunerAction(self._get_manager())

        exts = super(FusionsDiodePlugin, self)._my_task_extensions_default()

        ext1 = TaskExtension(
            task_id='pychron.fusions.diode',
            actions=[
                #                                     SchemaAddition(id='fusions_diode_group',
                #                                                    factory=lambda: GroupSchema(id='FusionsDiodeGroup'),
                #                                                    path='MenuBar/Extraction'
                #                                                    ),
                #                                     SchemaAddition(id='fusions_diode_group',
                #                                                   factory=lambda: Group(),
                #                                                   path='MenuBar/Extraction'
                #                                                   ),
                SchemaAddition(id='open_scan',
                               factory=factory_scan,
                               path='MenuBar/Laser'
                               #                                                 path='MenuBar/Extraction/FusionsDiodeGroup'
                ),
                SchemaAddition(id='open_autotune',
                               factory=factory_tune,
                               path='MenuBar/Laser'
                               #                                                 path='MenuBar/Extraction/FusionsDiodeGroup'
                ),
                SchemaAddition(id='calibration',
                               factory=lambda: Group(
                                   PowerMapAction(),
                                   PowerCalibrationAction(),
                                   PyrometerCalibrationAction(),
                               ),
                               path='MenuBar/Laser'
                ),
                SchemaAddition(
                    factory=TestDegasAction,
                    path='MenuBar/Laser'
                )
            ]
        )

        return exts + [ext1]

    def _preferences_panes_default(self):
        return [FusionsDiodePreferencesPane]


    def _task_factory(self):
    #        print self._get_manager()
        t = FusionsDiodeTask(manager=self._get_manager())
        return t

    #============= EOF =============================================
