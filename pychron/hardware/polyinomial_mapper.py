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
from numpy import poly1d
from scipy import optimize
from traits.api import HasTraits, List, Float
#============= standard library imports ========================
#============= local library imports  ==========================

class PolynomialMapper(HasTraits):
    """
    list of coefficients. see numpy.poly1d to see exactly how coefficients used
    coefficient = 1,2,3
        ==> 1*x^2+2*x+3
    """
    _coefficients = List

    output_low = Float(0)
    output_high = Float(100)

    _polynomial = None

    def set_coefficients(self, cs):
        self._coefficients = cs
        self._polynomial = poly1d(cs)

    def parse_coefficient_string(self, s):
        self.set_coefficients([float(si) for si in s.split(',')])

    def map_measured(self, v):
        """
            convert a measured value to an output value (Voltage -> Temp)
        """
        if self._polynomial:
            v = self._polynomial(v)
        return v

    def map_output(self, v):
        """
            convert an output value to measured value (Voltage <- Temp)
        """
        c=self._coefficients[:]
        c[-1] -= v
        return optimize.brentq(poly1d(c), self.output_low, self.output_high)
# ============= EOF =============================================



