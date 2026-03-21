# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import HasTraits, Property, Float, Enum, Str, Bool, Any
from uncertainties import ufloat, nominal_value, std_dev


# from pychron.pychron_constants import AGE_SCALARS, AGE_MA_SCALARS


# =============local library imports  ==========================


class ArArConstants(HasTraits):
    lambda_b = Property(depends_on="lambda_b_v, lambda_b_e")
    lambda_b_v = Float(4.962e-10)
    lambda_b_e = Float(9.3e-13)
    lambda_e = Property(depends_on="lambda_e_v, lambda_e_e")
    lambda_e_v = Float(5.81e-11)
    lambda_e_e = Float(1.6e-13)

    lambda_k = Property
    _lambda_k = Any
    lambda_Cl36 = Property(depends_on="lambda_36_v, lambda_Cl36_e")
    lambda_Cl36_v = Float(6.308e-9)
    lambda_Cl36_e = Float(0)
    lambda_Ar37 = Property(depends_on="lambda_Ar37_v, lambda_Ar37_e")
    lambda_Ar37_v = Float(0.01975)
    lambda_Ar37_e = Float(0)
    lambda_Ar39 = Property(depends_on="lambda_Ar39_v, lambda_Ar39_e")
    lambda_Ar39_v = Float(7.068e-6)
    lambda_Ar39_e = Float(0)

    atm4036 = Property(depends_on="atm4036_v,atm4036_e")
    atm4036_v = Float(295.5)
    atm4036_e = Float(0.5)

    atm4038 = Property(depends_on="atm4038_v,atm4038_e")
    atm4038_v = Float(1575)
    atm4038_e = Float(2)

    atm3836 = Property(depends_on="atm4038_v,atm4038_e,atm4036_v,atm4036_e")

    abundance_40K = 0.000117
    mK = 39.0983
    mO = 15.9994

    k3739_mode = Enum("Normal", "Fixed")
    fixed_k3739 = Property(depends_on="k3739_v, k3739_e")
    k3739_v = Float(0.01)
    k3739_e = Float(0.0001)

    age_units = Str
    # age_scalar = Property(depends_on='age_units')
    # ma_age_scalar = Property(depends_on='age_units')
    abundance_sensitivity = Float

    # ic_factors = Either(List, Str)

    atm4036_citation = Str  # 'Nier (1950)'
    atm4038_citation = Str  # 'Nier (1950)'
    lambda_b_citation = Str  # 'Min (2008)'
    lambda_e_citation = Str  # 'Min (2008)'
    lambda_Cl36_citation = Str  # 'Min (2008)'
    lambda_Ar39_citation = Str  # 'Min (2008)'
    lambda_Ar37_citation = Str  # 'Min (2008)'
    lambda_Cl36_citation = Str  # 'Min (2008)'
    use_irradiation_endtime = Bool

    allow_negative_ca_correction = Bool(True)
    trapped_atm4036 = None

    # cosmogenic
    use_cosmogenic_correction = Bool(False)
    solar3836 = Property(depends_on="solar3836_v,solar43836_e")
    solar3836_v = Float
    solar3836_e = Float

    cosmo3836 = Property(depends_on="cosmo3836_v, cosmo3836_e")
    cosmo3836_v = Float
    cosmo3836_e = Float

    def __init__(self, *args, **kw):
        try:
            from pychron.core.ui.preference_binding import bind_preference

            prefid = "pychron.arar.constants"

            for attr, prefattr in (
                ("lambda_b_v", "lambda_b"),
                ("lambda_b_e", "lambda_b_error"),
                ("lambda_e_v", "lambda_e"),
                ("lambda_e_e", "lambda_e_error"),
                ("lambda_Cl36_v", "lambda_cl36"),
                ("lambda_Cl36_e", "lambda_cl36_error"),
                ("lambda_Ar37_v", "lambda_ar37"),
                ("lambda_Ar37_e", "lambda_ar37_error"),
                ("lambda_Ar39_v", "lambda_ar39"),
                ("lambda_Ar39_e", "lambda_ar39_error"),
                ("atm4036_v", "ar40_ar36_atm"),
                ("atm4036_e", "ar40_ar36_atm_error"),
                ("atm4038_v", "ar40_ar38_atm"),
                ("atm4038_e", "ar40_ar38_atm_error"),
                ("k3739_mode", "ar37_ar39_mode"),
                ("k3739_v", "ar37_ar39"),
                ("k3739_e", "ar37_ar39_error"),
                ("atm4036_citation", "ar40_ar36_atm_citation"),
                ("atm4038_citation", "ar40_ar39_atm_citation"),
                ("lambda_b_citation", "lambda_b_citation"),
                ("lambda_e_citation", "lambda_e_citation"),
                ("lambda_Cl36_citation", "lambda_cl36_citation"),
                ("lambda_Ar37_citation", "lambda_ar37_citation"),
                ("lambda_Ar39_citation", "lambda_ar39_citation"),
            ):
                bind_preference(self, attr, "{}.{}".format(prefid, prefattr))

            for attr in (
                "use_irradiation_endtime",
                "age_units",
                "abundance_sensitivity",
                "allow_negative_ca_correction",
            ):
                bind_preference(self, attr, "{}.{}".format(prefid, attr))

        except (AttributeError, ImportError) as e:
            pass

        super(ArArConstants, self).__init__(*args, **kw)

    def scale_age(self, age, target=None, current=None):
        if target is None:
            target = self.age_units
        if current is None:
            current = self.age_units

        scalar = 1
        targetscalar = 1

        if current == "a":
            scalar = 1
        elif current == "ka":
            scalar = 1e3
        elif current == "Ma":
            scalar = 1e6
        elif current == "Ga":
            scalar = 1e9

        if target == "a":
            targetscalar = 1
        elif target == "ka":
            targetscalar = 1e-3
        elif target == "Ma":
            targetscalar = 1e-6
        elif target == "Ga":
            targetscalar = 1e-9

        return age * scalar * targetscalar

    def to_dict(self):
        d = dict()
        for ai in (
            "fixed_k3739",
            "atm4036",
            "atm4038",
            "lambda_Cl36",
            "lambda_Ar37",
            "lambda_Ar39",
            "lambda_k",
        ):
            v = getattr(self, ai)
            d[ai] = nominal_value(v)
            d["{}_err".format(ai)] = float(std_dev(v))

        d["abundance_sensitivity"] = self.abundance_sensitivity
        return d

    def cosmo_to_dict(self):
        d = {"use_cosmogenic_correction": self.use_cosmogenic_correction}
        for a in ("cosmo", "solar"):
            tag = "{}_3836".format(a)
            uv = getattr(self, tag)
            d[tag] = float(nominal_value(uv))
            d["{}_err".format(tag)] = float(std_dev(uv))

        return d

    def cosmo_from_dict(self, jd):
        for a in ("cosmo", "solar"):
            tag = "{}_3836".format(a)
            setattr(self, "{}_3836_v".format(a), jd.get(tag, 0))
            setattr(self, "{}_3836_e".format(a), jd.get("{}_err".format(tag), 0))

        self.use_cosmogenic_correction = jd.get("use_cosmogenic_correction", False)

    def set_cosmogenic_ratios(self, rs, rc):
        self.use_cosmogenic_correction = True
        self.solar3836_v, self.solar3836_e = rs
        self.cosmo3836_v, self.cosmo3836_e = rc

    @property
    def atm3836_v(self):
        return nominal_value(self.atm3836)

    @property
    def atm3836_e(self):
        return std_dev(self.atm3836)

    def _get_fixed_k3739(self):
        return self._get_ufloat("k3739")

    def _get_atm3836(self):
        return self.atm4036 / self.atm4038

    def _get_ufloat(self, attr):
        v = getattr(self, "{}_v".format(attr))
        e = getattr(self, "{}_e".format(attr))
        return ufloat(v, e, tag=attr)

    def _get_atm4036(self):
        if self.trapped_atm4036 is not None:
            return self.trapped_atm4036

        return self._get_ufloat("atm4036")

    def _get_atm4038(self):
        return self._get_ufloat("atm4038")

    def _get_solar3836(self):
        return self._get_ufloat("solar3836")

    def _get_cosmo3836(self):
        return self._get_ufloat("cosmo3836")

    def _get_lambda_Cl36(self):
        return self._get_ufloat("lambda_Cl36")

    def _get_lambda_Ar37(self):
        return self._get_ufloat("lambda_Ar37")

    def _get_lambda_Ar39(self):
        return self._get_ufloat("lambda_Ar39")

    def _get_lambda_b(self):
        return self._get_ufloat("lambda_b")

    def _get_lambda_e(self):
        return self._get_ufloat("lambda_e")

    def _get_lambda_k(self):
        k = self._lambda_k
        if not k:
            k = self.lambda_b + self.lambda_e
        return k

    def _set_lambda_k(self, k):
        self._lambda_k = k
        # return ufloat(k.nominal_value, k.std_dev)

    # def _get_age_scalar(self):
    #     try:
    #         return AGE_SCALARS[self.age_units]
    #     except KeyError:
    #         return 1
    #
    # def _get_ma_age_scalar(self):
    #     try:
    #         return AGE_MA_SCALARS[self.age_units]
    #     except KeyError:
    #         return 1
