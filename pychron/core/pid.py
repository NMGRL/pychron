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
# ============= standard library imports ========================
# ============= local library imports  ==========================

class PID(object):
    _integral_err = 0
    _prev_err = 0

    def __init__(self, kp=0.25, ki=0, kd=0, min_output=0, max_output=100):
        self.max_output = max_output
        self.min_output = min_output
        self.kd = kd
        self.ki = ki
        self.kp = kp

    def get_value(self, error, dt):
        self._integral_err += (error * dt)
        derivative = (error - self._prev_err) / dt
        output = (self.kp * error) + (self.ki * self._integral_err) + (self.kd * derivative)
        self._prev_err = error
        return min(self.max_output, max(self.min_output, output))

# ============= EOF =============================================
