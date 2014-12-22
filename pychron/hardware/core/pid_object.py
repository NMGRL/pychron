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



import time

from traits.api import HasTraits, Float
from traitsui.api import View


class PIDObject(HasTraits):
    Kp = Float(0.25)
    Ki = Float(0)
    Kd = Float(0)
    max_output = Float(100)

    _prev_time = Float(0, transient=True)
    _integral_err = Float(0, transiet=True)
    _prev_err = Float(0, transiet=True)

    def traits_view(self):
        return View('Kp', 'Ki', 'Kd', 'max_output')

    def iterate(self, error, dt):

        self._integral_err += (error * dt)
        derivative = (error - self._prev_err) / dt
        output = (self.Kp * error) + (self.Ki * self._integral_err) + (self.Kd * derivative)
        self._prev_err = error
        # limit the output to
        output = max(0, min(self.max_output, output))
        return output

    def get_value(self, err):
        if self._prev_time is None:
            self._prev_time = time.time()

        ct = time.time()
        dt = ct - self._prev_time
        self._prev_time = ct

        return self.iterate(err, dt)

#======== EOF ================================================================
