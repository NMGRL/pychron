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
from chaco.ticks import DefaultTickGenerator
from numpy import array
from numpy.core.umath import log10
from traits.api import Int
import math

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.graph import Graph


def intfilter(ticks):
    return [x for x in [x if x.is_integer() else math.ceil(x) for x in ticks] if x]


class IntTickGenerator(DefaultTickGenerator):
    def get_ticks(
        self,
        data_low,
        data_high,
        bounds_low,
        bounds_high,
        interval,
        use_endpoints=False,
        scale="linear",
    ):
        ticks = super(IntTickGenerator, self).get_ticks(
            data_low,
            data_high,
            bounds_low,
            bounds_high,
            interval,
            use_endpoints=use_endpoints,
            scale=scale,
        )
        # filter out non integer ticks
        ticks = intfilter(ticks)
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


class IntSparseTicks(SparseTicks):
    def get_ticks(self, *args, **kw):
        ticks = super(IntSparseTicks, self).get_ticks(*args, **kw)
        return intfilter(ticks)


class SparseLogTicks(DefaultTickGenerator):
    def get_ticks_and_labels(self, data_low, data_high, bounds_low, bounds_high):
        ticks = self.get_ticks(data_low, data_high, bounds_low, bounds_high, "auto")
        labels = array(["{:n}".format(t) for t in ticks])

        # only label 0.1,1,10,100,1000...
        try:
            labels[log10(ticks) % 1 != 0] = ""
        except ValueError:
            pass

        return ticks, labels

    def get_ticks(
        self,
        data_low,
        data_high,
        bounds_low,
        bounds_high,
        interval,
        use_endpoints=False,
        scale="log",
    ):
        i = 1
        while 1:
            if data_low < data_high:
                break
            data_low = min(10**-i, data_low)
            i += 1

        oticks = super(SparseLogTicks, self).get_ticks(
            data_low,
            data_high,
            bounds_low,
            bounds_high,
            interval,
            use_endpoints=use_endpoints,
            scale=scale,
        )
        ticks = oticks[oticks > data_low]

        return ticks


if __name__ == "__main__":
    g = Graph()
    pp = g.new_plot()
    g.new_series([1, 2, 3, 4, 5, 6, 7], [-1, 1, 10, 20, 30, 80, 105])

    pp.value_scale = "log"
    pp.value_axis.tick_generator = SparseLogTicks()
    g.configure_traits()
# ============= EOF =============================================
