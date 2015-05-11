# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import Bool, Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.extraction_line.extraction_line_manager import ExtractionLineManager
from pychron.extraction_line.status_monitor import StatusMonitor


class ClientExtractionLineManager(ExtractionLineManager):
    use_status_monitor = Bool
    status_monitor = Any

    def bind_preferences(self):
        super(ClientExtractionLineManager, self).bind_preferences()

        bind_preference(self, 'use_status_monitor', 'pychron.extraction_line.use_status_monitor')

    def start_status_monitor(self):
        self.info('starting status monitor')
        self.status_monitor.start(self.valve_manager)

    def stop_status_monitor(self):
        self.info('stopping status monitor')
        self.status_monitor.stop()

    def _reload_canvas_hook(self):
        vm = self.valve_manager
        if vm:
            vm.load_valve_states(refresh=False, force_network_change=False)
            vm.load_valve_lock_states(refresh=False)
            vm.load_valve_owners(refresh=False)

    def _check_ownership(self, name, requestor):
        return super(ClientExtractionLineManager, self)._check_ownership(name, requestor, force=True)

    def _activate_hook(self):
        if self.use_status_monitor:
            self.start_status_monitor()

    def _deactivate_hook(self):
        if self.use_status_monitor:
            self.stop_status_monitor()

    def _use_status_monitor_changed(self):
        if self.use_status_monitor:
            prefid = 'pychron.extraction_line'
            bind_preference(self.status_monitor, 'state_freq',
                            '{}.valve_state_frequency'.format(prefid))
            bind_preference(self.status_monitor, 'checksum_freq',
                            '{}.checksum_frequency'.format(prefid))
            bind_preference(self.status_monitor, 'lock_freq',
                            '{}.valve_lock_frequency'.format(prefid))
            bind_preference(self.status_monitor, 'owner_freq',
                            '{}.valve_owner_frequency'.format(prefid))
            bind_preference(self.status_monitor, 'update_period',
                            '{}.update_period'.format(prefid))
        else:
            if self.status_monitor.isAlive():
                self.status_monitor.stop()

    def _status_monitor_default(self):
        sm = StatusMonitor(valve_manager=self.valve_manager)
        return sm

    def _get_valve_manager_klass(self):
        from pychron.extraction_line.client_valve_manager import ClientValveManager

        return ClientValveManager

# ============= EOF =============================================



