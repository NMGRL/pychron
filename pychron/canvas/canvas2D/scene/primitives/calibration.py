# ===============================================================================
# Copyright 2016 ross
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

import math

from traits.has_traits import HasTraits
from traits.trait_types import Dict, Float
from traits.traits import Property


# ============= local library imports  ==========================


def calc_rotation(x1, y1, x2, y2):
    rise = y2 - y1
    run = x2 - x1
    return math.degrees(math.atan2(rise, run))


class CalibrationObject(HasTraits):
    tweak_dict = Dict
    cx = Float
    cy = Float
    rx = Float
    ry = Float

    rotation = Property(depends_on='rx,ry,_rotation')
    _rotation = Float
    center = Property(depends_on='cx,cy')
    scale = Float(1)

    def _set_rotation(self, rot):
        self._rotation = rot

    def _get_rotation(self):
        # if not (self.rx and self.rx):
        #     return self._rotation
        rot = self._rotation
        if not rot:
            rot = self.calculate_rotation(self.rx, self.ry)
        return rot

    def _get_center(self):
        return self.cx, self.cy

    def set_right(self, x, y):
        self.rx = x
        self.ry = y
        self._rotation = 0

    def set_center(self, x, y):
        self.cx = x
        self.cy = y

    def calculate_rotation(self, x, y, sense='east'):
        def rotation(a, b):
            return calc_rotation(self.cx, self.cy, a, b)

        if sense == 'west':
            print 'x={}, y={}, cx={}, cy={}'.format(x, y, self.cx, self.cy)
            if y > self.cy:
                rot = calc_rotation(self.cx, self.cy, x, y) - 180
            else:
                rot = calc_rotation(self.cx, self.cy, x, y) + 180
        elif sense == 'north':
            if x > self.cx:
                rot = rotation(x, -y)
            else:
                rot = rotation(y, -x)
        elif sense == 'south':
            rot = rotation(-y, x)
        else:
            rot = rotation(x, y)

        return rot
# ============= EOF =============================================
