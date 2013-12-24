#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from threading import Thread

from traits.api import HasTraits, Event, Property, Bool

# from pychron.core.ui.thread import Thread

#============= standard library imports ========================
#============= local library imports  ==========================

class ExecuteMixin(HasTraits):
    execute = Event
    execute_label = Property(depends_on='executing')
    executing = Bool

    def _get_execute_label(self):
        return 'Stop' if self.executing else 'Start'

    def _execute_fired(self):
        if self.executing:
            self._cancel_execute()
            self.executing = False
        else:
            if self._start_execute():
                self.executing = True
                t = Thread(target=self._do_execute)
                t.start()
                self._t = t

    def _cancel_execute(self):
        pass
    def _start_execute(self):
        return True

    def _do_execute(self):
        pass

    def isAlive(self):
        return self.executing

#============= EOF =============================================
