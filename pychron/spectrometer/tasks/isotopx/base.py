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

from pychron.spectrometer.tasks.base_spectrometer_plugin import BaseSpectrometerPlugin


class IsotopxSpectrometerPlugin(BaseSpectrometerPlugin):
    pass
    # id = 'pychron.spectrometer.argus'
    # spectrometer_manager_klass = ArgusSpectrometerManager
    # manager_name = 'argus_spectrometer_manager'
    # name = 'ArgusSpectrometer'

    # def start(self):
    #     super(IsotopxSpectrometerPlugin, self).start()
    #
    #     if to_bool(self.application.preferences.get('pychron.spectrometer.auto_open_readout')):
    #         from pychron.spectrometer.readout_view import new_readout_view
    #         #
    #         # spec = self.application.get_service(
    #         #     'pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager')
    #         # ro, v = new_readout_view(spectrometer=spec.spectrometer)
    #         rv = self.application.get_service(ReadoutView)
    #         v = new_readout_view(rv)
    #         open_view(rv, view=v)



    # ===============================================================================
    # defaults
    # ===============================================================================

    # def _readout_view_factory(self):
    #     v = ReadoutView(spectrometer=self.spectrometer_manager.spectrometer)
    #     return v
    #
    # def _preferences_panes_default(self):
    #     return [SpectrometerPreferencesPane]
    #
    # def _task_extensions_default(self):
    #
    #     def hop_action(name):
    #         def func():
    #             return HopsAction(name=name, hop_name=name)
    #
    #         return func
    #
    #     actions = []
    #
    #     for f in list_directory2(paths.hops_dir, extension='.yaml', remove_extension=True):
    #         actions.append(SchemaAddition(id='procedure.{}'.format(f),
    #                                       factory=hop_action(f),
    #                                       path='MenuBar/procedures.menu/hops.group'))
    #     ext = []
    #     if actions:
    #         actions.insert(0, SchemaAddition(id='hops.group',
    #                                          factory=lambda: SGroup(name='Hops', id='hops.group'),
    #                                          path='MenuBar/procedures.menu'))
    #
    #         ext.append(TaskExtension(actions=actions))
    #
    #     ta1 = TaskExtension(actions=[SchemaAddition(id='spectrometer.menu',
    #                                                 factory=lambda: SMenu(id='spectrometer.menu',
    #                                                                       name='Spectrometer'),
    #                                                 path='MenuBar',
    #                                                 before='window.menu',
    #                                                 after='tools.menu'),
    #                                  SchemaAddition(id='send_config',
    #                                                 factory=SendConfigAction,
    #                                                 path='MenuBar/spectrometer.menu'),
    #                                  SchemaAddition(id='view_readout',
    #                                                 factory=ViewReadoutAction,
    #                                                 path='MenuBar/spectrometer.menu'),
    #                                  SchemaAddition(id='edit_gains',
    #                                                 factory=EditGainsAction,
    #                                                 path='MenuBar/spectrometer.menu'),
    #                                  SchemaAddition(id='relood_table',
    #                                                 factory=ReloadMFTableAction,
    #                                                 path='MenuBar/spectrometer.menu'),
    #                                  SchemaAddition(id='mftable',
    #                                                 factory=MagnetFieldTableAction,
    #                                                 path='MenuBar/spectrometer.menu'),
    #                                  SchemaAddition(id='mftable_history',
    #                                                 factory=MagnetFieldTableHistoryAction,
    #                                                 path='MenuBar/spectrometer.menu')])
    #     si = TaskExtension(task_id='pychron.spectrometer.scan_inspector',
    #                        actions=[SchemaAddition(id='toggle_spectrometer_task',
    #                                                factory=ToggleSpectrometerTask,
    #                                                path='MenuBar/spectrometer.menu')])
    #
    #     sp = TaskExtension(task_id='pychron.spectrometer',
    #                        actions=[SchemaAddition(id='toggle_spectrometer_task',
    #                                                factory=ToggleSpectrometerTask,
    #                                                path='MenuBar/spectrometer.menu'),
    #                                 SchemaAddition(id='peak_center',
    #                                                factory=PeakCenterAction,
    #                                                path='MenuBar/spectrometer.menu'),
    #                                 SchemaAddition(id='define_peak_center',
    #                                                factory=DefinePeakCenterAction,
    #                                                path='MenuBar/spectrometer.menu'),
    #                                 SchemaAddition(id='coincidence',
    #                                                factory=CoincidenceScanAction,
    #                                                path='MenuBar/spectrometer.menu'),
    #                                 SchemaAddition(id='parameters',
    #                                                factory=SpectrometerParametersAction,
    #                                                path='MenuBar/spectrometer.menu')])
    #
    #     ext.extend((ta1, si, sp))
    #     return ext

# ============= EOF =============================================
