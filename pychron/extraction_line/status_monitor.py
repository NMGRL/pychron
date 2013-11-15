from pychron.loggable import Loggable
from threading import Event, Timer
from pyface.timer.do_later import do_later, do_after

class StatusMonitor(Loggable):
    valve_manager = None
    _stop_evt = None
    _clients = 0
    state_freq = 3
    lock_freq = 5
    owner_freq = 5
    period = 2
    def start(self):
        if not self._clients:
            if self._stop_evt:
                self._stop_evt.set()
                self._stop_evt.wait(0.25)

            self._stop_evt = Event()

            self._iter(1)
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

    def _iter(self, i):
        vm = self.valve_manager
        if not i % self.state_freq:
            vm.load_valve_states()

        if not i % self.lock_freq:
            vm.load_valve_lock_states()

        if not i % self.owner_freq:
            vm.load_valve_owners()

        if i > 100:
            i = 0
        if not self._stop_evt.isSet():
            do_after(self.period * 1000, self._iter, i + 1)
#            t=Timer(self.period, self._iter, (i+1,))
#            t.start()
