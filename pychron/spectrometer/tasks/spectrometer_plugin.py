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
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema import SMenu

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.spectrometer.spectrometer_manager import SpectrometerManager
from pychron.spectrometer.ion_optics_manager import IonOpticsManager
from pychron.spectrometer.scan_manager import ScanManager
from pychron.spectrometer.tasks.mass_cal.mass_calibration_task import MassCalibrationTask
from pychron.spectrometer.tasks.spectrometer_task import SpectrometerTask
from pychron.spectrometer.tasks.spectrometer_actions import PeakCenterAction, \
    CoincidenceScanAction, SpectrometerParametersAction, MagnetFieldTableAction
from pychron.spectrometer.tasks.spectrometer_preferences import SpectrometerPreferencesPane



#============= standard library imports ========================
#============= local library imports  ==========================

class SpectrometerPlugin(BaseTaskPlugin):
    #id = 'pychron.spectrometer'

    def get_spectrometer(self):
        spec = self.application.get_service('pychron.spectrometer.spectrometer_manager.SpectrometerManager')
        return spec.spectrometer

    def get_ion_optics(self):
        return self.application.get_service('pychron.spectrometer.ion_optics_manager.IonOpticsManager')

    def _factory_scan(self, *args, **kw):
        return ScanManager(application=self.application,
                           ion_optics_manager=self.get_ion_optics(),
                           spectrometer=self.get_spectrometer())

    def _factory_ion_optics(self, *args, **kw):
        return IonOpticsManager(application=self.application,
                                spectrometer=self.get_spectrometer())

    def _factory_spectrometer(self, *args, **kw):
        return SpectrometerManager(application=self.application)

    def _managers_default(self):
        """
        """
        app = self.application
        return [dict(name='spectrometer_manager',
                     manager=app.get_service(SpectrometerManager))]

    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.spectrometer',
                          task_group='hardware',
                          factory=self._task_factory,
                          name='Spectrometer',
                          image='prism'),
              TaskFactory(id='pychron.mass_calibration',
                          factory=self._mass_cal_task_factory,
                          name='Mass Calibration',
                          accelerator='Ctrl+Shift+M')]
        return ts

    def _mass_cal_task_factory(self):
        sm = self.application.get_service(SpectrometerManager)
        t = MassCalibrationTask(spectrometer_manager=sm)
        return t

    def _task_factory(self):
        sm = self.application.get_service(SpectrometerManager)
        #scm = self.application.get_service(ScanManager)
        scm=self._factory_scan()
        t = SpectrometerTask(manager=sm,
                             scan_manager=scm)
        return t

    #===============================================================================
    # defaults
    #===============================================================================
    def _preferences_panes_default(self):
        return [SpectrometerPreferencesPane]

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(
            protocol=SpectrometerManager,
            factory=self._factory_spectrometer)
        #so1 = self.service_offer_factory(
        #    protocol=ScanManager,
        #    factory=self._factory_scan)
        so2 = self.service_offer_factory(
            protocol=IonOpticsManager,
            factory=self._factory_ion_optics)

        #return [so, so1, so2]
        return [so, so2]

    def _my_task_extensions_default(self):
        return [
            TaskExtension(actions=[SchemaAddition(id='mftable',
                                                  factory=MagnetFieldTableAction,
                                                  path='MenuBar/Edit')]),
            TaskExtension(
                task_id='pychron.spectrometer',
                actions=[
                    SchemaAddition(id='Measure',
                                   factory=lambda: SMenu(id='Measure',
                                                         name='Measure'),
                                   path='MenuBar',
                                   before='Window',
                                   after='tools.menu'),
                    SchemaAddition(id='peak_center',
                                   factory=PeakCenterAction,
                                   path='MenuBar/Measure'),
                    SchemaAddition(id='coincidence',
                                   factory=CoincidenceScanAction,
                                   path='MenuBar/Measure'),
                    SchemaAddition(id='parameters',
                                   factory=SpectrometerParametersAction,
                                   path='MenuBar/Edit')])]

        #============= EOF =============================================
