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
from traits.api import Float, Property
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.abstract_device import AbstractDevice


class LinearAxis(AbstractDevice):
    position = Property(depends_on='_position')
    _position = Float

    min_value = Float(0.0)
    max_value = Float(100.0)

    min_limit = Property(depends_on='_position')
    max_limit = Property(depends_on='_position')

    _slewing = False

    def set_home(self):
        if self._cdevice:
            self._cdevice.set_home()

    def set_position(self, v, **kw):
        if self._cdevice:
            self._cdevice.set_position(v, **kw)
            # self.add_consumable((self._cdevice.set_position, v, kw))

    # def relative_move(self, v):
    #     self.set_position(self._position + v)
    def is_slewing(self):
        return self._slewing

    def is_stalled(self):
        if self._cdevice:
            return self._cdevice.stalled()

    def slew(self, modifier):
        if self._cdevice:
            self._slewing = True
            self._cdevice.slew(modifier)

    def stop(self):
        if self._cdevice:
            self._slewing = False
            self._cdevice.stop_drive()

    def _get_min_limit(self):
        return abs(self._position - self.min_value) < 1e-5

    def _get_max_limit(self):
        return abs(self._position - self.max_value) < 1e-5

    def _get_position(self):
        return float('{:0.3f}'.format(self._position))

    def _set_position(self, v):
        self._position = v
        if self._cdevice:
            self.set_position(v)

# ============= EOF =============================================
