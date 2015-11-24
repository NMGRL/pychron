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
from traits.api import Dict

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle


class StateableRectangle(RoundedRectangle):
    states = Dict

    def set_state(self, state):
        if isinstance(state, bool):
            state = 'open' if state else 'closed'

        state_dict = self.states[state]

        self._set_dimensions(state_dict.get('dimension'))
        self._set_translation(state_dict.get('translation'))
        self.request_layout()

    def _set_dimensions(self, wh):
        if wh:
            self.width, self.height = wh

    def _set_translation(self, xy):
        if xy:
            self.x, self.y = xy


class Gate(StateableRectangle):
    pass


class Funnel(StateableRectangle):
    pass

# ============= EOF =============================================
