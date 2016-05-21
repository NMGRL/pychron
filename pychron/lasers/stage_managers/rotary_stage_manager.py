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
from traits.api import Float, Instance
# ============= standard library imports ========================
import math
# ============= local library imports  ==========================
from pychron.hardware.motion_controller import ZeroDisplacementException, TargetPositionError
from pychron.hardware.rotary_drive import RotaryDrive
from pychron.lasers.stage_managers.stage_manager import StageManager
from pychron.lasers.stage_managers.video_stage_manager import VideoStageManager


class BaseRotaryStageManager:
    """
    0 degrees is defined to be 3 oclock
    90 degrees is 12

    """

    # the angle in degrees of the windows center
    window_theta = Float

    rotary_drive = Instance(RotaryDrive)

    def _move_to_hole(self, key, correct_position=True, user_entry=False):
        self.info('Move to hole {} type={}'.format(key, str(type(key))))
        self.temp_hole = key
        self.temp_position = self.stage_map.get_hole_pos(key)
        pos = self.stage_map.get_corrected_hole_pos(key)
        self.info('position {}'.format(pos))
        autocentered_position = False
        if pos is not None:

            if abs(pos[0]) < 1e-6:
                pos = self.stage_map.get_hole_pos(key)
                # map the position to calibrated space
                pos = self.get_calibrated_position(pos, key=key)
            else:
                # check if this is an interpolated position
                # if so probably want to do an autocentering routine
                hole = self.stage_map.get_hole(key)
                if hole.interpolated:
                    self.info('using an interpolated value')
                else:
                    self.info('using previously calculated corrected position')
                    autocentered_position = True

            rotation = self._calculate_rotation(*pos)
            self.rotary_drive.set_angle(rotation)

            npos = self._calculate_xy_position(*pos)
            try:
                self.stage_controller.linear_move(block=True, raise_zero_displacement=True, *npos)
            except TargetPositionError, e:
                self.warning('Move to {} failed'.format(pos))
                self.parent.emergency_shutoff(str(e))
                return
            except ZeroDisplacementException:
                correct_position = False

            self._move_to_hole_hook(key, correct_position,
                                    autocentered_position)
            self.finish_move_to_hole(user_entry)
            self.info('Move complete')

    def _calculate_xy_position(self, x, y):
        distance = (x ** 2 + y ** 2) ** 0.5
        return distance, 0

    def _calculate_rotation(self, x, y):
        theta = math.atan2(y, x)
        theta = math.degrees(theta) - self.window_theta
        return theta


class RotaryStageManager(BaseRotaryStageManager, StageManager):
    pass


class RotaryVideoStageManager(BaseRotaryStageManager, VideoStageManager):
    pass

# ============= EOF =============================================
