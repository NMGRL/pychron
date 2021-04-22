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
from traits.api import HasTraits, List, Float, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import csv_to_floats


class PolynomialMapperMixin(HasTraits):
    poly_mapper = None
    mapped_name = Str

    def load_mapping(self, config):
        conv = 'Conversion'
        if config.has_section(conv):
            pmapper = self.factory(config, conv)
            self.poly_mapper = pmapper
            self.set_attribute(config, 'mapped_name', conv, 'name')

            if self.mapped_name:
                u = self.config_get(config, conv, 'units', default='')
                self.graph_ytitle = '{} ({})'.format(self.mapped_name.capitalize(), u)

    def factory(self, config, section):
        pmapper = PolynomialMapper()
        coeffs = self.config_get(config, section, 'coefficients')
        pmapper.parse_coefficient_string(coeffs)
        pmapper.output_low = self.config_get(config, section, 'output_low', cast='float')
        pmapper.output_high = self.config_get(config, section, 'output_high', cast='float')

        return pmapper


class BaseMapper(HasTraits):
    def map_measured(self, v):
        raise NotImplementedError

    def map_output(self, v):
        raise NotImplementedError



class PolynomialMapper(BaseMapper):
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
        self.set_coefficients(csv_to_floats(s))

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



