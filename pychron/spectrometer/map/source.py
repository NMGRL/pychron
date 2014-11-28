# ===============================================================================
# Copyright 2011 Jake Ross
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

#============= enthought library imports =======================
from traits.api import Float, HasTraits
from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================


class MapSource(HasTraits):
    nominal_hv = Float(4500)
    current_hv = Float(4500)

    def read_hv(self):
        return self._read_value('GetHighVoltage', 'current_hv')

    def _set_value(self, name, v):
        r = self.ask('{} {}'.format(name, v))
        if r is not None:
            if r.lower().strip() == 'ok':
                return True

    def _read_value(self, name, value):
        r = self.ask(name)
        try:
            setattr(self, value, float(r))
            return getattr(self, value)
        except (ValueError, TypeError):
            pass

    def sync_parameters(self):
        self.read_hv()

    def traits_view(self):
        v = View(Item('nominal_hv'),
                 Item('current_hv', style='readonly'))
        return v

    # ===============================================================================
    # property get/set
    # ===============================================================================
# ============= EOF =============================================
