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
from traits.api import HasTraits, Int, Float
from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================

class LinearMapper(HasTraits):
    low_step = Int(0)
    high_step = Int(1)

    low_data = Float(0)
    high_data = Float(1)
    _scale = 1
    def map_data(self, steps):
        self._compute_scale()
        return (steps - self.low_step) / self._scale + self.low_data

    def map_steps(self, data):
        self._compute_scale()
        return (data - self.low_data) * self._scale + self.low_step

    def _compute_scale(self):
        data_range = self.high_data - self.low_data
        step_range = self.high_step - self.low_step
        self._scale = step_range / data_range
#============= EOF =============================================
