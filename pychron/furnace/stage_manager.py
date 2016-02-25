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

import time
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.furnace_canvas import FurnaceCanvas
from pychron.hardware.linear_axis import LinearAxis
from pychron.paths import paths
from pychron.stage.maps.furnace_map import FurnaceStageMap
from pychron.stage.stage_manager import BaseStageManager


class SampleLinearHolder(LinearAxis):
    def jitter(self, turns=0.125, n=20, freq=10):
        """
        :param turns: fractional turns
        :param n: number of times to move
        :param freq: frequency of jitter. i.e changes of direction per second
        :return:
        """
        p = 1 / float(freq)
        for i in xrange(n):
            turns *= -1
            self._cdevice.move_relative(turns, convert_turns=True)
            time.sleep(p)


class BaseFurnaceStageManager(BaseStageManager):
    root = paths.furnace_map_dir
    stage_map_klass = FurnaceStageMap

    def __init__(self, *args, **kw):
        super(BaseFurnaceStageManager, self).__init__(*args, **kw)
        self.tray_calibration_manager.style = 'Linear'


class NMGRLFurnaceStageManager(BaseFurnaceStageManager):
    sample_linear_holder = Instance(SampleLinearHolder)

    def jitter(self):
        self.sample_linear_holder.jitter()

    def set_sample_dumped(self):
        hole = self.stage_map.get_hole(self.calibrated_position_entry)
        if hole:
            hole.analyzed = True
            self.canvas.request_redraw()

    def get_current_position(self):
        if self.sample_linear_holder:
            x = self.sample_linear_holder.position
            return x, 0

    def goto_position(self, v):
        self.move_to_hole(v)

    def in_motion(self):
        return self.sample_linear_holder.moving()

    def relative_move(self, ax_key, direction, distance):
        self.sample_linear_holder.slew(direction * distance)

    def key_released(self):
        self.sample_linear_holder.stop()

    # private
    def _move_to_hole(self, key, correct_position=True):
        self.info('Move to hole {} type={}'.format(key, str(type(key))))
        pos = self.stage_map.get_hole_pos(key)
        if pos:
            self.temp_hole = key
            self.temp_position = pos

            x, y = self.get_calibrated_position(pos, key=key)
            self.info('hole={}, position={}, calibrated_position={}'.format(key, pos, (x, y)))

            self.sample_linear_holder.position = x
            self.sample_linear_holder.move_absolute(x)

            self.info('Move complete')
            self.update_axes()  # update_hole=False)
        else:
            self.debug('invalid hole {}'.format(key))

    def _update_axes(self):
        pass

        # v = self.sample_linear_holder.update_current_position()

    def _canvas_factory(self):
        c = FurnaceCanvas(sample_linear_holder=self.sample_linear_holder)
        return c

    def _sample_linear_holder_default(self):
        d = SampleLinearHolder(name='sample_linear_holder', configuration_dir_name='furnace')
        return d

# ============= EOF =============================================
