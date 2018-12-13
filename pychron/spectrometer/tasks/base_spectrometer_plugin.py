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
from __future__ import absolute_import

import os

from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import Any

from pychron.core.helpers.filetools import glob_list_directory
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.envisage.tasks.list_actions import SpectrometerScriptAction, HopsAction
from pychron.paths import paths
from pychron.spectrometer.base_spectrometer_manager import BaseSpectrometerManager
from pychron.spectrometer.ion_optics.ion_optics_manager import IonOpticsManager
from pychron.spectrometer.readout_view import ReadoutView
from pychron.spectrometer.scan_manager import ScanManager
from pychron.spectrometer.tasks.spectrometer_actions import PopulateMFTableAction, SendConfigAction, ViewReadoutAction, \
    EditGainsAction, ReloadMFTableAction, MagnetFieldTableAction, MagnetFieldTableHistoryAction, ToggleSpectrometerTask, \
    PeakCenterAction, DefinePeakCenterAction, CoincidenceScanAction, SpectrometerParametersAction
from pychron.spectrometer.tasks.spectrometer_preferences import SpectrometerPreferencesPane
from pychron.spectrometer.tasks.spectrometer_task import SpectrometerTask


class BaseSpectrometerPlugin(BaseTaskPlugin):
    spectrometer_manager = Any
    spectrometer_manager_klass = None
    task_klass = SpectrometerTask
    manager_name = ''
    scan_manager = Any
    ion_optics_manager = Any

    def start(self):
        super(BaseSpectrometerPlugin, self).start()
        if self.spectrometer_manager:
            self.spectrometer_manager.spectrometer.start()

    # ===============================================================================
    # tests
    # ===============================================================================
    def test_communication(self):
        manager = self.spectrometer_manager
        return manager.test_connection()

    def test_intensity(self):
        manager = self.spectrometer_manager
        ret = manager.test_connection(force=False)
        if ret and ret[0]:
            ret = manager.test_intensity()

        return ret

    def _inspector_task_factory(self):
        from pychron.spectrometer.tasks.inspector.scan_inspector_task import ScanInspectorTask

        t = ScanInspectorTask()
        return t

    def _mass_cal_task_factory(self):
        from pychron.spectrometer.tasks.mass_cal.mass_calibration_task import MassCalibrationTask

        t = MassCalibrationTask(spectrometer_manager=self.spectrometer_manager)
        return t

    def _task_factory(self):
        t = self.task_klass(manager=self.spectrometer_manager,
                            scan_manager=self.scan_manager,
                            application=self.application)
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
        so = self.service_offer_factory(protocol=BaseSpectrometerManager,
                                        factory=self._factory_spectrometer)
        so1 = self.service_offer_factory(protocol=IonOpticsManager,
                                         factory=self._factory_ion_optics)

        so2 = self.service_offer_factory(protocol=ScanManager,
                                         factory=self._factory_scan_manager)

        so3 = self.service_offer_factory(protocol=ReadoutView,
                                         factory=self._readout_view_factory)
        return [so, so1, so2, so3]

    def _preferences_default(self):
        return self._preferences_factory('spectrometer')

    def _preferences_panes_default(self):
        return [SpectrometerPreferencesPane]

    def _readout_view_factory(self):
        v = ReadoutView(spectrometer=self.spectrometer_manager.spectrometer)
        return v

    def _managers_default(self):
        """
        """
        return [dict(name=self.manager_name,
                     plugin_name=self.name,
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

    def _hops_ext(self):
        def hop_action(name):
            def func():
                return HopsAction(name=name, hop_name=name)

            return func

        actions = []

        for f in glob_list_directory(paths.hops_dir, extension='.yaml', remove_extension=True):
            actions.append(SchemaAddition(id='procedure.{}'.format(f),
                                          factory=hop_action(f),
                                          path='MenuBar/procedures.menu/hops.group'))

        if actions:
            m = SchemaAddition(id='procedures.menu',
                               before='window.menu',
                               after='tools.menu',
                               factory=lambda: SMenu(name='Procedures', id='procedures.menu'),
                               path='MenuBar')
            g = SchemaAddition(id='hops.group',
                               factory=lambda: SGroup(name='Hops', id='hops.group'),
                               path='MenuBar/procedures.menu')
            actions.insert(0, g)
            actions.insert(0, m)

            ext = TaskExtension(actions=actions)
            return ext

    def _scripts_ext(self):
        def script_action(name):
            def func():
                p = os.path.join(paths.spectrometer_scripts_dir, '{}.py'.format(name))
                return SpectrometerScriptAction(name=name, script_path=p)

            return func

        actions = []

        for f in glob_list_directory(paths.spectrometer_scripts_dir, extension='.py', remove_extension=True):
            actions.append(SchemaAddition(id='spectrometer_script.{}'.format(f),
                                          factory=script_action(f),
                                          path='MenuBar/procedures.menu/spectrometer_script.group'))
        if actions:
            m = SchemaAddition(id='procedures.menu',
                               before='window.menu',
                               after='tools.menu',
                               factory=lambda: SMenu(name='Procedures', id='procedures.menu'),
                               path='MenuBar')
            g = SchemaAddition(id='spectrometer_script.group',
                               factory=lambda: SGroup(name='Spectrometer',
                                                      id='spectrometer_script.group'),
                               path='MenuBar/procedures.menu')

            actions.insert(0, g)
            actions.insert(0, m)

            ext = TaskExtension(actions=actions)
            return ext

    def _task_extensions_default(self):

        ext = []
        hopext = self._hops_ext()
        if hopext:
            ext.append(hopext)

        scriptext = self._scripts_ext()
        if scriptext:
            ext.append(scriptext)

        ta1 = TaskExtension(actions=[SchemaAddition(id='spectrometer.menu',
                                                    factory=lambda: SMenu(id='spectrometer.menu',
                                                                          name='Spectrometer'),
                                                    path='MenuBar',
                                                    before='window.menu',
                                                    after='tools.menu'),
                                     SchemaAddition(id='update_mftable',
                                                    path='MenuBar/spectrometer.menu',
                                                    factory=PopulateMFTableAction),
                                     SchemaAddition(id='send_config',
                                                    factory=SendConfigAction,
                                                    path='MenuBar/spectrometer.menu'),
                                     SchemaAddition(id='view_readout',
                                                    factory=ViewReadoutAction,
                                                    path='MenuBar/spectrometer.menu'),
                                     SchemaAddition(id='edit_gains',
                                                    factory=EditGainsAction,
                                                    path='MenuBar/spectrometer.menu'),
                                     SchemaAddition(id='relood_table',
                                                    factory=ReloadMFTableAction,
                                                    path='MenuBar/spectrometer.menu'),
                                     SchemaAddition(id='mftable',
                                                    factory=MagnetFieldTableAction,
                                                    path='MenuBar/spectrometer.menu'),
                                     SchemaAddition(id='mftable_history',
                                                    factory=MagnetFieldTableHistoryAction,
                                                    path='MenuBar/spectrometer.menu')])
        si = TaskExtension(task_id='pychron.spectrometer.scan_inspector',
                           actions=[SchemaAddition(id='toggle_spectrometer_task',
                                                   factory=ToggleSpectrometerTask,
                                                   path='MenuBar/spectrometer.menu')])

        sp = TaskExtension(task_id='pychron.spectrometer',
                           actions=[SchemaAddition(id='toggle_spectrometer_task',
                                                   factory=ToggleSpectrometerTask,
                                                   path='MenuBar/spectrometer.menu'),
                                    SchemaAddition(id='peak_center',
                                                   factory=PeakCenterAction,
                                                   path='MenuBar/spectrometer.menu'),
                                    SchemaAddition(id='define_peak_center',
                                                   factory=DefinePeakCenterAction,
                                                   path='MenuBar/spectrometer.menu'),
                                    SchemaAddition(id='coincidence',
                                                   factory=CoincidenceScanAction,
                                                   path='MenuBar/spectrometer.menu'),
                                    SchemaAddition(id='parameters',
                                                   factory=SpectrometerParametersAction,
                                                   path='MenuBar/spectrometer.menu')])

        ext.extend((ta1, si, sp))
        return ext
# ============= EOF =============================================
