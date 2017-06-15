# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Any, Event, Property, Bool
from pyface.qt.QtCore import QThread
# from traitsui.api import View, Item, spring, ButtonEditor, HGroup
# ============= standard library imports ========================
from numpy import linspace
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from threading import Thread


# from pychron.spectrometer.spectrometer import Spectrometer

class SpectrometerTask(Loggable):
    spectrometer = Any
    execute_button = Event
    execute_label = Property(depends_on='_alive')
    _alive = Bool
    execution_thread = None
    graph = Any

    def _get_execute_label(self):
        return 'Stop' if self.isAlive() else 'Start'

    def isAlive(self):
        return self._alive

    def stop(self):
        self._alive = False
        self.execution_thread = None

    def _execute_button_fired(self):
        if self.isAlive():
            self.stop()
            self._end()
        else:
            self.execute()

    def execute(self):
        self.debug('execute', self.__class__.__name__)
        self._alive = True
        t = QThread(name=self.__class__.__name__, target=self._execute)
        t.start()
        self.execution_thread = t
        self.debug('execution thread. {}'.format(t))
        return t

    def _execute(self):
        pass

    def _end(self):
        pass

    def _graph_factory(self):
        pass

    def _graph_default(self):
        return self._graph_factory()

    def _calc_step_values(self, start, end, width):
        sign = 1 if start < end else -1
        nsteps = abs(end - start + width * sign) / width
        self.debug('calculated step values: start={}, end={}, width={}, nsteps={}'.format(start, end, width, nsteps))
        return linspace(start, end, nsteps)

# ============= EOF =============================================
