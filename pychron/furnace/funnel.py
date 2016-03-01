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
import json

from traits.api import Int

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class NMGRLFunnel(CoreDevice):
    _simulation_funnel_up = True

    def in_up_position(self):
        if not self.simulation:
            return self.ask('InUpPosition') == 'True'
        else:
            return self._simulation_funnel_up

    def in_down_position(self):
        if not self.simulation:
            return self.ask('InDownPosition') == 'False'
        else:
            return not self._simulation_funnel_up

    def read_position(self):
        d = {'drive': 'funnel'}
        d = json.dumps(d)
        pos = self.ask('GetPosition {}'.format(d))
        try:
            return float(pos)
        except (TypeError, ValueError):
            pass

    def set_value(self, pos):
        d = {'drive': 'funnel', 'position': pos}
        d = json.dumps(d)
        self.ask('SetPosition {}'.format(d))

    def lower(self):
        self.ask('LowerFunnel')

    def raise_(self):
        self.ask('RaiseFunnel')


# ============= EOF =============================================
