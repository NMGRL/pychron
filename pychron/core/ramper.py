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
import time
import math
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup


# ============= standard library imports ========================
# ============= local library imports  ==========================


def calculate_steps(duration, period=1):
    return int(math.ceil(duration / float(period)))


class StepRamper(object):
    def ramp(self, func, start, end, step, period=1):
        current = start
        canceled = False
        while 1:
            ct = time.time()
            if current >= end:
                break

            if not func(current):
                canceled = True
                break

            current += step

            time.sleep(max(0, period - (time.time() - ct)))

        if not canceled:
            func(end)


class Ramper(object):
    def ramp(self, func, start, end, duration, rate=0, period=1):
        """
            rate = units/s
            duration= s

            use rate if specified
        """
        st = time.time()
        if end is not None:
            if rate:
                duration = abs(start - end) / float(rate)

            if duration:
                self._ramp(func, start, end, duration, period)

        return time.time() - st

    def _ramp(self, func, start, end, duration, period):
        st = time.time()
        i = 1

        step = period * (end - start) / float(duration)

        while (time.time() - st) < duration:
            ct = time.time()
            v = start + i * step
            if func(i, v):
                time.sleep(max(0, period - (time.time() - ct)))
                i += 1
            else:
                break

# ============= EOF =============================================
