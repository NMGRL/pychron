# ===============================================================================
# Copyright 2020 ross
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
from pychron.core.geometry.reference_point import ReferenceHole
from pychron.stage.calibration.hole_calibrator import HoleCalibrator


class IrregularHoleCalibrator(HoleCalibrator):
    def _handle_end_calibrate(self, d, x, y, canvas):

        sm = self.stage_map
        for pos, (x, y) in self.points:
            sm.set_hole_correction(pos, x, y)

        sm.dump_correction_file()
        self.info('updated {} correction file'.format(sm.name))
        d['clear_corrections'] = False
        return d

    def _get_point(self, sp):
        smap = self.stage_map
        vs = [si.id for si in smap.sample_holes]
        rp = ReferenceHole(sp, valid_holes=vs)
        info = rp.edit_traits()
        if info.result:
            return rp.hole, sp

            # # get the x,y position for this hole
            #     h = smap.get_hole(hole)
            #     refp = h.x, h.y
            #     return refp, sp
# ============= EOF =============================================
