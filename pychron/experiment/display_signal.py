#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Str, Float, Property, Either
from traitsui.api import View, Item
from pychron.helpers.formatting import calc_percent_error
#============= standard library imports ========================
#============= local library imports  ==========================
class DisplaySignal(HasTraits):
    isotope = Str
    detector = Str
    fit = Str
    baseline_fit = 'SEM'

    raw_value = Float
    raw_error = Float
    intercept_value = Float
    intercept_error = Float
    baseline_value = Float
    baseline_error = Float
    blank_value = Float
    blank_error = Float
    signal_value = Float
    signal_error = Float
    error_component = Float

    raw_error_percent = Property
    intercept_error_percent = Property
    baseline_error_percent = Property
    blank_error_percent = Property

    ic_factor_value = Float
    ic_factor_error = Float

    def _get_raw_error_percent(self):
        v = self.raw_value
        e = self.raw_error
        return calc_percent_error(v, e)
    def _get_baseline_error_percent(self):
        v = self.baseline_value
        e = self.baseline_error
        return calc_percent_error(v, e)
    def _get_blank_error_percent(self):
        v = self.blank_value
        e = self.blank_error
        return calc_percent_error(v, e)

    def _get_intercept_error_percent(self):
        v = self.intercept_value
        e = self.intercept_error
        return calc_percent_error(v, e)

class DisplayEntry(DisplaySignal):
    # set to None so not displayed
    signal_value = None
    signal_error = None
    ic_factor_value = None
    ic_factor_error = None

class DisplayValue(HasTraits):
    value = Either(Str, Float)
    error = Float
    name = Str

class DisplayRatio(DisplayValue):
    pass
#============= EOF =============================================
