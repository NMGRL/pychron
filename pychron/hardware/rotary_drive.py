# ===============================================================================
# Copyright 2016 Jake Ross
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
from pychron.hardware.core.abstract_device import AbstractDevice


class RotaryDrive(AbstractDevice):
    use_hysteresis_correction = True
    hysteresis_correction = 5  # in degrees

    def set_angle(self, theta):
        """

        :param theta: angle in degrees
        :return:
        """
        self.debug('set angle {}'.format(theta))
        if self._cdevice:

            if self.use_hysteresis_correction:
                if theta > 180:
                    hc = self._angle_to_steps(self.hysteresis_correction)
                    steps = self._angle_to_steps(theta - 360)
                    self._cdevice.move_relative(steps + hc)
                    velocity = self._cdevice.velocity
                    self._cdevice.move_relative(-hc, velocity=velocity * self.hysteresis_velocity_scalar)
                else:
                    self._cdevice.move_relative(self._angle_to_steps(theta))
            else:
                steps = self._angle_to_steps(theta)
                self._cdevice.move_absolute(steps)

    def _angle_to_steps(self, theta):
        return self._cdevice.steps_per_turn * theta / 360.

# ============= EOF =============================================
