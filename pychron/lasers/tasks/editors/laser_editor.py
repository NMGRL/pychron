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
from traits.api import Any, Bool

from pychron.envisage.tasks.base_editor import BaseTraitsEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
class LaserEditor(BaseTraitsEditor):
    component = Any
    _execute_thread = None
    was_executed = False
    _laser_manager = Any
    completed=Bool(False)

    def stop(self):
        pass

    def do_execute(self, lm):
        self.completed=False
        self._laser_manager = lm
        return self._do_execute()

    def _do_execute(self):
        pass

    def block(self):
        if self._execute_thread:
            self._execute_thread.join()
            self.completed=True

# ============= EOF =============================================
