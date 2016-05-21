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
    def set_angle(self, theta):
        """

        :param theta: angle in degrees
        :return:
        """
        self.debug('set angle {}'.format(theta))
        if self._cdevice:
            steps = self._angle_to_steps(theta)

            # sign = self._calculate_direction(steps)
            # velocity = self._cdevice.velocity
            # self._cdevice.move_absolute(steps, velocity=sign*velocity)

            self._cdevice.move_absolute(steps)

    def _calculate_direction(self, pos):
        cpos = self._cdevice.get_position()
        return 1 if cpos - pos < 0 else -1

    def _angle_to_steps(self, theta):
        return self._cdevice.steps_per_turn * theta / 360.

# ============= EOF =============================================
