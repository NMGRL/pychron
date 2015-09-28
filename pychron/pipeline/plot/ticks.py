# ===============================================================================
# Copyright 2012 Jake Ross
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
import math

from numpy.core.umath import log10
from numpy import hstack
from traits.api import Int
from chaco.ticks import DefaultTickGenerator


# ============= standard library imports ========================
# from numpy import log10
# ============= local library imports  ==========================
class IntTickGenerator(DefaultTickGenerator):
    def get_ticks(self, data_low, data_high, bounds_low,
                  bounds_high, interval, use_endpoints=False,
                  scale='linear'):
        ticks = super(IntTickGenerator, self).get_ticks(data_low, data_high, bounds_low,
                                                        bounds_high, interval, use_endpoints=use_endpoints,
                                                        scale=scale)
        # filter out non integer ticks
        ticks = filter(lambda x: x % 1 == 0, ticks)
        return ticks


class SparseTicks(DefaultTickGenerator):
    step = Int(2)

    def get_ticks(self, *args, **kw):
        ticks = super(SparseTicks, self).get_ticks(*args, **kw)
        s = self.step
        try:
            if len(ticks) > max(6, s + 2):
                return ticks[1:-1:s]
            elif len(ticks) > 4:
                return ticks[1:]
            else:
                return ticks
        except IndexError:
            return ticks


class SparseLogTicks(DefaultTickGenerator):
    def get_ticks(self, *args, **kw):
        oticks = super(SparseLogTicks, self).get_ticks(*args, **kw)

        # get only 0.1,1,10,100,1000...
        ticks = oticks[oticks > 0]
        ticks = ticks[log10(ticks) % 1 == 0]

        if ticks.shape[0] == 1:
            tlow = 10 ** math.floor(math.log10(ticks[0]))
            if tlow == ticks[0]:
                tlow = 10 ** math.floor(math.log10(ticks[0]) - 1)

            ticks = hstack(([tlow], ticks))
            ticks = hstack((ticks, [10 ** math.ceil(math.log10(oticks[-1]))]))

            ticks[0] = max(oticks[0], ticks[0])

        return ticks

# ============= EOF =============================================
