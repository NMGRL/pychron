# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Either, Float, Int, Property, Bool, Any

# ============= standard library imports ========================
from uncertainties import std_dev, nominal_value


# ============= local library imports  ==========================


class NamedValue(HasTraits):
    name = Str
    value = Either(Str, Float, Int, None)
    units = Str


class ComputedValue(NamedValue):
    error = Either(Str, Float, Int)
    tag = Str
    display_value = Bool(True)
    sig_figs = Int(5)
    value_tag = Str
    uvalue = Any

    def _uvalue_changed(self):
        self.value = nominal_value(self.uvalue)
        self.error = std_dev(self.uvalue)


class DetectorRatio(ComputedValue):
    ic_factor = Either(Float, Str)
    detectors = Str
    noncorrected_value = Float
    noncorrected_error = Float
    calc_ic = Property(depends_on="value")
    ref_ratio = Float

    def _get_calc_ic(self):
        return self.noncorrected_value / self.ref_ratio


class ExtractionValue(NamedValue):
    conditional_visible = Bool(False)


class MeasurementValue(NamedValue):
    pass


# ============= EOF =============================================
