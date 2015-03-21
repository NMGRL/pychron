# ===============================================================================
# Copyright 2014 Jake Ross
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
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.spectrometer.base_spectrometer_manager import BaseSpectrometerManager
from pychron.spectrometer.ion_optics_manager import IonOpticsManager
from pychron.spectrometer.scan_manager import ScanManager
from pychron.spectrometer.tasks.spectrometer_task import SpectrometerTask


class BaseSpectrometerPlugin(BaseTaskPlugin):
    spectrometer_manager = Any
    spectrometer_manager_klass = None
    manager_name = ''
    scan_manager = Any
    ion_optics_manager = Any

    def _inspector_task_factory(self):
        from pychron.spectrometer.tasks.inspector.scan_inspector_task import ScanInspectorTask
        t= ScanInspectorTask()
        return t

    def _mass_cal_task_factory(self):
        from pychron.spectrometer.tasks.mass_cal.mass_calibration_task import MassCalibrationTask
        t = MassCalibrationTask(spectrometer_manager=self.spectrometer_manager)
        return t

    def _task_factory(self):
        t = SpectrometerTask(manager=self.spectrometer_manager,
                             scan_manager=self.scan_manager)
        return t

    def _factory_spectrometer(self):
        return self.spectrometer_manager

    def _factory_ion_optics(self):
        return self.ion_optics_manager

    def _factory_scan_manager(self):
        return self.scan_manager

    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.spectrometer',
                          task_group='hardware',
                          factory=self._task_factory,
                          accelerator="Ctrl+'",
                          name='Spectrometer',
                          image='spectrum_emission'),
              TaskFactory(id='pychron.mass_calibration',
                          factory=self._mass_cal_task_factory,
                          name='Mass Calibration',
                          accelerator='Ctrl+Shift+M'),
              TaskFactory(id='pychron.spectrometer.scan_inspector',
                          factory=self._inspector_task_factory,
                          name='Scan Inspector')]
        return ts

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(
            protocol = BaseSpectrometerManager,
            # protocol=self.spectrometer_manager_klass,
            factory=self._factory_spectrometer)
        so1 = self.service_offer_factory(
            protocol=IonOpticsManager,
            factory=self._factory_ion_optics)

        so2 = self.service_offer_factory(
            protocol=ScanManager,
            factory=self._factory_scan_manager)

        return [so, so1, so2]

    def _managers_default(self):
        """
        """
        return [dict(name=self.manager_name,
                     manager=self.spectrometer_manager)]

    def _spectrometer_manager_default(self):
        sm = self.spectrometer_manager_klass(application=self.application)
        return sm

    def _ion_optics_manager_default(self):
        im = IonOpticsManager(application=self.application,
                              spectrometer=self.spectrometer_manager.spectrometer)
        return im

    def _scan_manager_default(self):
        sm = ScanManager(application=self.application,
                         spectrometer=self.spectrometer_manager.spectrometer,
                         ion_optics_manager=self.ion_optics_manager)
        return sm

# ============= EOF =============================================



