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
from pychron.stage.maps.base_stage_map import BaseStageMap, SampleHole


class FurnaceStageMap(BaseStageMap):
    def _hole_factory(self, hi, line, shape, dimension, valid_holes):
        ah = ''
        args = line.split(',')

        y = 0
        if len(args) == 1:
            hole = str(hi + 1)
            x = float(args[0])
        elif len(args) == 2:
            hole = args[0]
            x = float(args[1])
        else:
            self.warning(
                'invalid stage map file. {}. Problem with line {}: {}'.format(self.file_path, hi + 3, line))
            return

        return SampleHole(id=hole,
                          x=float(x),
                          y=float(y),
                          associated_hole=ah,
                          render='x' if hole in valid_holes else '',
                          shape=shape,
                          dimension=dimension)

# ============= EOF =============================================
