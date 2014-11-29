# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.geometry.reference_point import  ReferenceHole
from pychron.lasers.stage_managers.calibration.free_calibrator import FreeCalibrator


class HoleCalibrator(FreeCalibrator):
    stage_map = Any
    def _get_point(self, sp):
        smap = self.stage_map
        vs = [si.id for si in smap.sample_holes]
        rp = ReferenceHole(sp, valid_holes=vs)
        info = rp.edit_traits()
        if info.result:
#             refp = rp.x, rp.y
            hole = rp.hole
            # get the x,y position for this hole
            if hole in vs:
                h = smap.get_hole(hole)
                refp = h.x, h.y
                return refp, sp



# ============= EOF =============================================
