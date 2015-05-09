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
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema import SMenu
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import to_bool
from pychron.spectrometer.readout_view import ReadoutView
from pychron.spectrometer.tasks.base_spectrometer_plugin import BaseSpectrometerPlugin
from pychron.spectrometer.thermo.spectrometer_manager import ArgusSpectrometerManager
from pychron.spectrometer.tasks.spectrometer_actions import PeakCenterAction, \
    CoincidenceScanAction, SpectrometerParametersAction, MagnetFieldTableAction, MagnetFieldTableHistoryAction, \
    ToggleSpectrometerTask, EditGainsAction, SendConfigAction, ViewReadoutAction
from pychron.spectrometer.tasks.spectrometer_preferences import SpectrometerPreferencesPane


class ArgusSpectrometerPlugin(BaseSpectrometerPlugin):
    id = 'pychron.spectrometer.argus'
    spectrometer_manager_klass = ArgusSpectrometerManager
    manager_name = 'argus_spectrometer_manager'
    name = 'ArgusSpectrometer'

    def start(self):
        super(ArgusSpectrometerPlugin, self).start()

        if to_bool(self.application.preferences.get('pychron.spectrometer.auto_open_readout')):
            from pychron.spectrometer.readout_view import new_readout_view
            #
            # spec = self.application.get_service(
            #     'pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager')
            # ro, v = new_readout_view(spectrometer=spec.spectrometer)
            rv = self.application.get_service(ReadoutView)
            v = new_readout_view(rv)
            self.application.open_view(rv, view=v)

    # ===============================================================================
    # tests
    # ===============================================================================
    def test_communication(self):
        manager = self.spectrometer_manager
        t = manager.test_connection()
        return 'Passed' if t else 'Failed'

    def test_intensity(self):
        manager = self.spectrometer_manager
        t = manager.test_connection(force=False)
        if t:
            tt = manager.test_intensity()
            return 'Passed' if tt else 'Failed'

    # ===============================================================================
    # defaults
    # ===============================================================================

    def _readout_view_factory(self):
        v = ReadoutView(spectrometer=self.spectrometer_manager.spectrometer)
        return v

    def _preferences_panes_default(self):
        return [SpectrometerPreferencesPane]

    def _task_extensions_default(self):
        return [
            TaskExtension(
                actions=[
                    SchemaAddition(id='spectrometer.menu',
                                   factory=lambda: SMenu(id='spectrometer.menu',
                                                         name='Spectrometer'),
                                   path='MenuBar',
                                   before='window.menu',
                                   after='tools.menu'),

                    SchemaAddition(id='send_config',
                                   factory=SendConfigAction,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='view_readout',
                                   factory=ViewReadoutAction,
                                   path='MenuBar/spectrometer.menu'),

                    SchemaAddition(id='edit_gains',
                                   factory=EditGainsAction,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='mftable',
                                   factory=MagnetFieldTableAction,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='mftable_history',
                                   factory=MagnetFieldTableHistoryAction,
                                   path='MenuBar/spectrometer.menu')]),
            # SchemaAddition(id='db_mftable_history',
            # factory=DBMagnetFieldTableHistoryAction,
            #                path='MenuBar/spectrometer.menu')]),
            TaskExtension(
                task_id='pychron.spectrometer.scan_inspector',
                actions=[
                    SchemaAddition(id='toggle_spectrometer_task',
                                   factory=ToggleSpectrometerTask,
                                   path='MenuBar/spectrometer.menu')]),
            TaskExtension(
                task_id='pychron.spectrometer',
                actions=[
                    SchemaAddition(id='toggle_spectrometer_task',
                                   factory=ToggleSpectrometerTask,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='peak_center',
                                   factory=PeakCenterAction,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='coincidence',
                                   factory=CoincidenceScanAction,
                                   path='MenuBar/spectrometer.menu'),
                    SchemaAddition(id='parameters',
                                   factory=SpectrometerParametersAction,
                                   path='MenuBar/spectrometer.menu')])]

        # ============= EOF =============================================
        # def _service_offers_default(self):
        # """
        #     """
        #     so = self.service_offer_factory(
        #         protocol=ArgusSpectrometerManager,
        #         factory=self._factory_spectrometer)
        #     #so1 = self.service_offer_factory(
        #     #    protocol=ScanManager,
        #     #    factory=self._factory_scan)
        #     so2 = self.service_offer_factory(
        #         protocol=IonOpticsManager,
        #         factory=self._factory_ion_optics)
        #
        #     #return [so, so1, so2]
        #     return [so, so2]
        # def get_spectrometer(self):
        #     spec = self.application.get_service('pychron.spectrometer.thermo.spectrometer_manager.ArgusSpectrometerManager')
        #     return spec.spectrometer
        #
        # def get_ion_optics(self):
        #     return self.application.get_service('pychron.spectrometer.ion_optics_manager.IonOpticsManager')

        # def _factory_scan(self, *args, **kw):
        #     return ScanManager(application=self.application,
        #                        ion_optics_manager=self.get_ion_optics(),
        #                        spectrometer=self.get_spectrometer())
        #
        # def _factory_ion_optics(self, *args, **kw):
        #     return IonOpticsManager(application=self.application,
        #                             spectrometer=self.get_spectrometer())

        # def _factory_spectrometer(self, *args, **kw):
        #     return ArgusSpectrometerManager(application=self.application)

        # def _managers_default(self):
        #     """
        #     """
        #     app = self.application
        #     return [dict(name='argus_spectrometer_manager',
        #                  manager=app.get_service(ArgusSpectrometerManager))]
        # def _tasks_default(self):
        #     ts = [TaskFactory(id='pychron.spectrometer',
        #                       task_group='hardware',
        #                       factory=self._task_factory,
        #                       name='Spectrometer',
        #                       image='prism'),
        #           TaskFactory(id='pychron.mass_calibration',
        #                       factory=self._mass_cal_task_factory,
        #                       name='Mass Calibration',
        #                       accelerator='Ctrl+Shift+M')]
        #     return ts
        #
        # def _mass_cal_task_factory(self):
        #     # sm = self.application.get_service(ArgusSpectrometerManager)
        #     t = MassCalibrationTask(spectrometer_manager=self.spectrometer_manager)
        #     return t
        #
        # def _task_factory(self):
        #     # sm = self.application.get_service(ArgusSpectrometerManager)
        #     #scm = self.application.get_service(ScanManager)
        #     # scm = self._factory_scan()
        #     t = SpectrometerTask(manager=self.spectrometer_manager,
        #                          scan_manager=self.scan_manager)
        #     return t