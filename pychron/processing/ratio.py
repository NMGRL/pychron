# ===============================================================================
# Copyright 2014 Jake Ross
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
from uncertainties import ufloat
#============= local library imports  ==========================


class RatioElement(object):
    def __init__(self, v):
        if not isinstance(v, tuple):
            v = (v, 0)
        self.value = ufloat(*v)

    # def __add__(self, other):
    #     return self.value + other
    #
    # def __sub__(self, other):
    #     return self.value - other
    #
    def __mul__(self, other):
        return self.value * other

    def __div__(self, other):
        return self.value / other

    # def __radd__(self, other):
    #     return self.__add__(other)
    #
    # def __rsub__(self, other):
    #     return other - self.value

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rdiv__(self, other):
        return other / self.value


class Ratio(object):
    nom = None
    den = None

    def __init__(self, n, d):
        self.nom = RatioElement(n)
        self.den = RatioElement(d)

    @property
    def value(self):
        try:
            return self.nom / self.den
        except ZeroDivisionError:
            return

#============= EOF =============================================

