# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================


from threading import Event

from pyface.timer.do_later import do_after
from traits.api import Int

from pychron.loggable import Loggable


class StatusMonitor(Loggable):
    # valve_manager = None
    _stop_evt = None
    _clients = 0

    state_freq = Int(3)
    checksum_freq = Int(3)

    lock_freq = Int(5)
    owner_freq = Int(5)
    update_period = Int(1)

    def start(self, vm):
        if not self._clients:
            if self._stop_evt:
                self._stop_evt.set()
                self._stop_evt.wait(0.25)

            self._stop_evt = Event()

            self._iter(1, vm)
        else:
            self.debug('Monitor already running')

        self._clients += 1

    def isAlive(self):
        if self._stop_evt:
            return not self._stop_evt.isSet()

    def stop(self):
        self._clients -= 1

        if not self._clients:
            self._stop_evt.set()
            self.debug('Status monitor stopped')
        else:
            self.debug('Alive clients {}'.format(self._clients))

    def _iter(self, i, vm):
        if vm is None:
            self.debug('No valve manager')
            return

        if not i % self.state_freq:
            vm.load_valve_states()

        if not i % self.lock_freq:
            vm.load_valve_lock_states()

        if not i % self.owner_freq:
            vm.load_valve_owners()

        if not i % self.checksum_freq:
            if not vm.state_checksum:
                self.debug('State checksum failed')

        #         vm.load_valve_states()
        #         vm.load_valve_lock_states()
        #         vm.load_valve_owners()

        if i > 100:
            i = 0
        if not self._stop_evt.isSet():
            do_after(self.update_period * 1000, self._iter, i + 1, vm)

            # ============= EOF =============================================