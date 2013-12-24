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
from traits.api import HasTraits, Property, List, String
#============= standard library imports ========================
from numpy import poly1d
from scipy import optimize
from pychron.core.helpers.formatting import floatfmt

#============= local library imports  ==========================

class MeterCalibration(HasTraits):
    coeff_string = Property(String(enter_set=True, auto_set=False))
    coefficients = List
    bounds = None

    output_low = 0
    output_high = 100

    def __init__(self, *args, **kw):
        if args:
            coeffs = args[0]
            if isinstance(coeffs, str):
                coeffs = self._parse_coeff_string(coeffs)

            self.coefficients = coeffs

        super(MeterCalibration, self).__init__(**kw)

    def _parse_coeff_string(self, coeffs):
        try:
            return map(float, coeffs.split(','))
        except:
            pass

    def _validate_coeff_string(self, v):
        return self._parse_coeff_string(v)

    def _set_coeff_string(self, v):
        if v:
            self.coefficients = v

    def _get_coeff_string(self):
        c = ''
        if self.coefficients:

            c = ', '.join(map(lambda x: floatfmt(x, 3), self.coefficients))
        return c

    def dump_coeffs(self):
        return ','.join(map(str, self.coefficients))

    def get_input(self, response):
        '''
            return the input required to produce the requested response
        '''
        if self.bounds:
            for c, b in zip(self.coefficients, self.bounds):
                if b[0] < response <= b[1]:
                    break
            else:
                closest = 0
                min_d = 1000
                for i, b in enumerate(self.bounds):
                    d = min(abs(b[0] - response), abs(b[1] - response))
                    if d < min_d:
                        closest = i
                c = self.coefficients[closest]
        else:
            c = self.coefficients

        # say y=ax+b (watts=a*power_percent+b)
        # calculate x for a given y
        # solvers solve x for y=0
        # we want x for y=power, therefore
        # subtract the requested power from the intercept coeff (b)
        # find the root of the polynominal

        if c is not None and len(c):
            c[-1] -= response
            power = optimize.brentq(poly1d(c), self.output_low,
                                               self.output_high)
            c[-1] += response
        else:
            power = response

        return power

    def print_string(self):
        return ','.join(['{}={:0.3e}'.format(*c) for c in zip('abcdefg', self.coefficients)])
#============= EOF =============================================
