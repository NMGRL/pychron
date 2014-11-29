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
from traits.api import List, Any, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class ExperimentUndoer(Loggable):
    run_factory = Any
    _stack = List

    @on_trait_change('run_factory:edit_event')
    def _handle_edit_event(self, evt):
        self.push(evt['attribute'], evt)

    def undo(self):
        if self._stack:
            self._undo()
            self.update_event = True
        else:
            self.warning('no action to undo')

    def push(self, action, state):
        self._stack.insert(0, (action, state))

    def _undo(self):
        action, state = self._stack.pop(0)
        self.debug('undoing action: {}'.format(action))
        if action == 'add runs':
            q = self.queue
            for ri in state:
                q.remove(ri)
        else:
            attr = state['attribute']
            for ri, v in state['previous_state']:
                setattr(ri, attr, v)

        self.run_factory.refresh()


# ============= EOF =============================================

