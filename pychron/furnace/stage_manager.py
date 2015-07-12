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
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.furnace_canvas import FurnaceCanvas
from pychron.hardware.linear_axis import LinearAxis
from pychron.paths import paths
from pychron.stage.maps.furnace_map import FurnaceStageMap
from pychron.stage.stage_manager import BaseStageManager


class Dumper(LinearAxis):
    def dump(self):
        pass


class FurnaceStageManager(BaseStageManager):
    dumper = Instance(Dumper)
    funnel = Instance(LinearAxis)
    root = paths.furnace_map_dir
    stage_map_klass = FurnaceStageMap

    def __init__(self, *args, **kw):
        super(FurnaceStageManager, self).__init__(*args, **kw)
        self.tray_calibration_manager.style = 'Linear'

    def get_current_position(self):
        if self.dumper:
            x = self.dumper.position
            return x, 0

    def goto_position(self, v):
        self.move_to_hole(v)

    # private
    def _move_to_hole(self, key, correct_position=True):
        self.info('Move to hole {} type={}'.format(key, str(type(key))))
        self.temp_hole = key
        self.temp_position = pos = self.stage_map.get_hole_pos(key)

        x, y = self.get_calibrated_position(pos, key=key)
        self.info('hole={}, position={}, calibrated_position={}'.format(key, pos, (x, y)))

        # self.dumper.linear_move(x)
        self.info('Move complete')
        self.update_axes()  # update_hole=False)

    def _update_axes(self):
        pass

        # v = self.dumper.update_current_position()

    def _canvas_factory(self):
        c = FurnaceCanvas(dumper=self.dumper)
        return c

    def _dumper_default(self):
        d = Dumper(name='dumper', configuration_dir_name='furnace')
        return d

    def _funnel_default(self):
        f = LinearAxis(name='funnel', configuration_dir_name='furnace')
        return f

# ============= EOF =============================================
