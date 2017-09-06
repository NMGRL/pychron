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
import time
from threading import Event, Thread

from traits.api import Int, List

from pychron.globals import globalv
from pychron.loggable import Loggable


class StatusMonitor(Loggable):
    # valve_manager = None
    _stop_evt = None
    _finished_evt = None
    _clients = List

    state_freq = Int(3)
    checksum_freq = Int(3)

    lock_freq = Int(5)
    owner_freq = Int(5)
    update_period = Int(1)

    def start(self, oid, vm):
        self.debug('start {}'.format(oid))
        if not self._clients:
            p = self.update_period
            s, c, l, o = self.state_freq, self.checksum_freq, self.lock_freq, self.owner_freq
            self.debug('StatusMonitor period={}. '
                       'Frequencies(state={}, checksum={}, lock={}, owner={})'.format(p, s, c, l, o))
            if self._stop_evt:
                self._stop_evt.set()
                time.sleep(1.5*self.update_period)
                # self._stop_evt.wait(self.update_period)

            self._stop_evt = Event()
            t = Thread(target=self._run, args=(vm,))
            t.setName('StatusMonitor({})'.format(oid))
            t.setDaemon(True)
            t.start()
        else:
            self.debug('Monitor already running')

        if oid not in self._clients:
            self._clients.append(oid)

    def isAlive(self):
        if self._stop_evt:
            return not self._stop_evt.isSet()

    def stop(self, oid, block=True):
        self.debug('stop {}'.format(oid))
        try:
            self._clients.remove(oid)
        except ValueError:
            pass

        if not self._clients:
            self._stop_evt.set()
            self.debug('Status monitor stopped')

            if block:
                time.sleep(1.5*self.update_period)
                # self._stop_evt.wait(2*self.update_period)

        else:
            self.debug('Alive clients {}'.format(self._clients))

    def _run(self, vm):
        if vm is None:
            self.debug('No valve manager')
        else:
            i = 0
            while 1:
                time.sleep(self.update_period)
                if self._stop_evt.is_set():
                    break

                if self._iter(i, vm):
                    break

                if i > 100:
                    i = 0
                i += 1

        self.debug('Status monitor finished')

    def _iter(self, i, vm):
        if globalv.valve_debug:
            self.debug('status monitor iteration i={}'.format(i))
        if self._stop_evt.is_set():
            self.debug('stop_event set. no more iterations')
            return True

        delay = self.update_period/2.
        if self.state_freq and not i % self.state_freq:
            if globalv.valve_debug:
                self.debug('load valve states')
            vm.load_valve_states()
            time.sleep(delay)

        if self.lock_freq and not i % self.lock_freq:
            if globalv.valve_debug:
                self.debug('load lock states')
            vm.load_valve_lock_states()
            time.sleep(delay)

        if self.owner_freq and not i % self.owner_freq:
            if globalv.valve_debug:
                self.debug('load owners')
            vm.load_valve_owners()
            time.sleep(delay)

        if self.checksum_freq and not i % self.checksum_freq:
            if not vm.state_checksum:
                self.debug('State checksum failed')

        return self._stop_evt.is_set()

        # if i > 100:
        #     i = 0
        # if not self._stop_evt.is_set():
        #     do_after(self.update_period * 1000, self._iter, i + 1, vm)

# ============= EOF =============================================
