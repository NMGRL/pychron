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

from traits.api import Str, Property, cached_property, Float

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import ufloat

from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope


class NonDBAnalysis(Analysis):
    # record_id = Str
    uage = Property(depends_on="age, age_err")
    uuid = Str
    sample = Str

    k39_err = Float
    rad40_err = Float
    kca_err = Float
    radiogenic_yield_err = Float

    @classmethod
    def from_csv_record(cls, ri):
        obj = cls()
        for a in (
            "age",
            "age_err",
            "group",
            "aliquot",
            "sample",
            "label_name",
            "k39",
            "k39_err",
            "rad40",
            "rad40_err",
            "kca",
            "kca_err",
            "radiogenic_yield",
            "radiogenic_yield_err",
            "x",
            "y",
            "x_err",
            "y_err",
        ):
            try:
                setattr(obj, a, getattr(ri, a))
            except AttributeError:
                pass

        for k in ("ar40", "ar39", "ar36"):
            iso = Isotope(k.capitalize(), "Det")
            try:
                iso.interference_corrected_value = ufloat(
                    getattr(ri, k), getattr(ri, "{}_err".format(k))
                )
            except AttributeError:
                continue

            obj.isotopes[k.capitalize()] = iso

        obj.record_id = ri.runid

        return obj

    def get_computed_value(self, attr):
        if attr in ("k39", "rad40", "kca", "radiogenic_yield"):
            return self._as_ufloat(attr)
        else:
            return ufloat(0, 0)

    def _as_ufloat(self, attr):
        return ufloat(getattr(self, attr), getattr(self, "{}_err".format(attr)))

    @cached_property
    def _get_uage(self):
        return self._as_ufloat("age")


class FileAnalysis(NonDBAnalysis):
    pass


class InterpretedAgeAnalysis(NonDBAnalysis):
    pass


# ============= EOF =============================================
