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
from envisage.extension_point import ExtensionPoint
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.action.action import Action
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import HasTraits, Bool, Instance, List, Dict

from pychron.core.helpers.importtools import import_klass
from pychron.core.helpers.strtools import to_bool
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.envisage.view_util import open_view
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.hardware.flag_manager import FlagManager
from pychron.hardware.tasks.hardware_preferences import HardwarePreferencesPane
from pychron.hardware.tasks.hardware_task import HardwareTask


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Preference(HasTraits):
    pass


class SerialPreference(Preference):
    auto_find_handle = Bool
    auto_write_handle = Bool


class DevicePreferences(HasTraits):
    serial_preference = Instance(SerialPreference)

    def _serial_preference_default(self):
        return SerialPreference()


class OpenFlagManagerAction(Action):
    name = 'Flag Manager'

    def perform(self, event):
        app = event.task.window.application
        man = app.get_service('pychron.hardware.flag_manager.FlagManager')

        open_view(man)


class HardwarePlugin(BaseTaskPlugin):
    id = 'pychron.hardware.plugin'
    managers = ExtensionPoint(List(Dict),
                              id='pychron.hardware.managers')

    # my_managers = List(contributes_to='pychron.hardware.managers')

    sources = List(contributes_to='pychron.video.sources')

    # def _my_managers_default(self):
    #     return [dict(name='hardware', manager=self._hardware_manager_factory())]

    #    def _system_lock_manager_factory(self):
    #        return SystemLockManager(application=self.application)
    _remote_hardware_manager = None
    # _remote_hardware_manager = Instance('pychron.remote_hardware.remote_hardware_manager.RemoteHardwareManager')
    # _hardware_manager = Instance('pychron.managers.hardware_manager.HardwareManager')

    def start(self):
        # if self.managers:
        from pychron.envisage.initialization.initializer import Initializer

        dp = DevicePreferences()
        afh = self.application.preferences.get('pychron.hardware.auto_find_handle')
        awh = self.application.preferences.get('pychron.hardware.auto_write_handle')
        if afh is not None:
            dp.serial_preference.auto_find_handle = to_bool(afh)
            dp.serial_preference.auto_write_handle = to_bool(awh)

        ini = Initializer(device_prefs=dp)
        for m in self.managers:
            ini.add_initialization(m)

        # any loaded managers will be registered as services
        if not ini.run(application=self.application):
            self.application.exit()
            # self.application.starting
            return

        # create the hardware proxy server
        ehs = to_bool(self.application.preferences.get('pychron.hardware.enable_hardware_server'))
        if ehs:
            # use_tx = to_bool(self.application.preferences.get('pychron.hardware.use_twisted', True))
            use_tx = True
            if use_tx:
                from pychron.tx.server import TxServer
                rhm = TxServer()
                node = self.application.preferences.node('pychron.hardware')
                ports = eval(node.get('ports', '[]'))
                factories = eval(node.get('factories', '[]'))
                for protocol in eval(node.get('pnames', '[]')):
                    factory = import_klass(factories[protocol])
                    port = int(ports[protocol])

                    exc = rhm.add_endpoint(port, factory(self.application))
                    if exc:
                        msg = 'Failed starting Command Server for "{}:{}". Please check that multiple ' \
                              'instances of pychron are not running on this computer. ' \
                              'Exception: {}'.format(protocol, port, exc)
                        self.warning_dialog(msg)
                    else:
                        self.info('Added Pychron Proxy Service: {}:{}'.format(protocol, port))

            # else:
            #     from pychron.remote_hardware.remote_hardware_manager import RemoteHardwareManager
            #     rhm = RemoteHardwareManager(application=self.application)

            self._remote_hardware_manager = rhm
            rhm.bootstrap()

    def stop(self):
        if self._remote_hardware_manager:
            self._remote_hardware_manager.kill()

        if self.managers:
            for m in self.managers:
                man = m['manager']
                if man:
                    man.kill()

        for s in self.application.get_services(ICoreDevice):
            if s.is_scanable:
                s.stop_scan()

    def _factory(self):
        task = HardwareTask(application=self.application)
        return task

    def _flag_manager_factory(self):
        return FlagManager(application=self.application)

    # def _hardware_manager_factory(self):
    #     return HardwareManager(application=self.application)

    # def _remote_hardware_manager_factory(self):
    #     return RemoteHardwareManager(application=self.application)

    def _service_offers_default(self):

        # so_hm = self.service_offer_factory(
        #     protocol=HardwareManager,
        #     factory=self._hardware_manager_factory)
        #
        # so_rhm = self.service_offer_factory(
        #     protocol=RemoteHardwareManager,
        #     factory=self._remote_hardware_manager_factory)

        so_fm = self.service_offer_factory(
            protocol=FlagManager,
            factory=self._flag_manager_factory)
        #        return [so, so1, so2]
        # return [so_hm, so_rhm, so_fm]
        # return [so_hm, so_fm]
        return [so_fm]

    def _preferences_panes_default(self):
        return [HardwarePreferencesPane]

    def _sources_default(self):
        return [('pvs://localhost:1081', 'Hardware')]

    def _task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(id='Flag Manager',
                                                      factory=OpenFlagManagerAction,
                                                      path='MenuBar/tools.menu'), ])]

    def _tasks_default(self):
        return [TaskFactory(id='tasks.hardware',
                            name='Hardware',
                            factory=self._factory,
                            image='configure-2',
                            task_group='hardware')]

# ============= EOF =============================================
