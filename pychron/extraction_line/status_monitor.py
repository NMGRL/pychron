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
from pyface.timer.do_later import do_after
from traits.api import Int, List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from threading import Event
from pychron.loggable import Loggable


class StatusMonitor(Loggable):
    # valve_manager = None
    _stop_evt = None
    _clients = List

    state_freq = Int(3)
    checksum_freq = Int(3)

    lock_freq = Int(5)
    owner_freq = Int(5)
    update_period = Int(1)

    # def __init__(self, *args, **kw):
    #     super(StatusMonitor, self).__init__(*args, **kw)
    #     self._clients = []

    def start(self, oid, vm):
        if not self._clients:
            s, c, l, o = self.state_freq, self.checksum_freq, self.lock_freq, self.owner_freq
            self.debug('StatusMonitor period={}. '
                       'Frequencies(state={}, checksum={}, lock={}, owner={})'.format(s, c, l, o))
            if self._stop_evt:
                self._stop_evt.set()
                self._stop_evt.wait(0.25)

            self._stop_evt = Event()

            self._iter(1, vm)
        else:
            self.debug('Monitor already running')

        if oid not in self._clients:
            self._clients.append(oid)

    def isAlive(self):
        if self._stop_evt:
            return not self._stop_evt.isSet()

    def stop(self, oid):
        # self._clients -= 1
        try:
            self._clients.remove(oid)
        except ValueError:
            pass

        if not self._clients:
            self._stop_evt.set()
            self.debug('Status monitor stopped')
        else:
            self.debug('Alive clients {}'.format(self._clients))

    def _iter(self, i, vm):
        if self._stop_evt.is_set():
            return

        if vm is None:
            self.debug('No valve manager')
            return

        if self.state_freq and not i % self.state_freq:
            vm.load_valve_states()

        if self.lock_freq and not i % self.lock_freq:
            vm.load_valve_lock_states()

        if self.owner_freq and not i % self.owner_freq:
            vm.load_valve_owners()

        if self.checksum_freq and not i % self.checksum_freq:
            if not vm.state_checksum:
                self.debug('State checksum failed')

        if i > 100:
            i = 0
        if not self._stop_evt.is_set():
            do_after(self.update_period * 1000, self._iter, i + 1, vm)

# ============= EOF =============================================
