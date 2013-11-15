#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Int
from chaco.ticks import DefaultTickGenerator
#============= standard library imports ========================
from numpy import hstack, log10
#============= local library imports  ==========================


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
        ticks = super(SparseLogTicks, self).get_ticks(*args, **kw)
        # get only 0.1,1,10,100,1000...
        ticks = ticks[log10(ticks) % 1 == 0]
        return ticks

#============= EOF =============================================
