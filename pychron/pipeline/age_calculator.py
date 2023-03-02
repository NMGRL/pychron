# ===============================================================================
# Copyright 2020 ross
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
from traits.api import Float, Bool, Button
from traitsui.api import View, UItem, Item, HGroup, VGroup, Readonly
from uncertainties import std_dev, nominal_value, ufloat

from pychron.core.pychron_traits import BorderVGroup
from pychron.loggable import Loggable
from pychron.processing.arar_constants import ArArConstants
from pychron.processing.argon_calculations import (
    calculate_f,
    age_equation,
    calculate_arar_decay_factors,
)

arar_constants = ArArConstants()


class AgeCalculator(Loggable):
    ar40 = Float(100)
    ar39 = Float(10)
    ar39_corrected = Float(10)
    ar38 = Float(1)
    ar37 = Float(1)
    ar37_corrected = Float(1)
    ar36 = Float(0.001)

    correct_for_decay = Bool
    decay_days = Float(10)
    decay_factor_39 = Float
    decay_factor_37 = Float

    j = Float(1e-3)
    j_err = Float

    age = Float
    age_err = Float

    calculate_button = Button

    def _calculate(self):
        dc37 = nominal_value(arar_constants.lambda_Ar37)
        dc39 = nominal_value(arar_constants.lambda_Ar39)

        # pi, ti, ti_p, _, _
        a, b = calculate_arar_decay_factors(
            dc37, dc39, [(1, 1, self.decay_days, None, None)]
        )

        self.decay_factor_37, self.decay_factor_39 = float(a), float(b)

        self.ar37_corrected = self.ar37 * self.decay_factor_37
        self.ar39_corrected = self.ar39 * self.decay_factor_39
        isos = (
            ufloat(getattr(self, attr), 0)
            for attr in ("ar40", "ar39_corrected", "ar38", "ar37_corrected", "ar36")
        )

        f, f_wo_irrad, non_ar_isotopes, computed, interference_corrected = calculate_f(
            isos, self.decay_days
        )
        uage = age_equation(ufloat(self.j, self.j_err), f)

        self.trait_set(age=float(nominal_value(uage)), age_err=float(std_dev(uage)))

    def _calculate_button_fired(self):
        self._calculate()

    def traits_view(self):
        isogrp = BorderVGroup(
            Item("ar40"),
            HGroup(Item("ar39"), Readonly("ar39_corrected")),
            Item("ar38"),
            HGroup(Item("ar37"), Readonly("ar37_corrected")),
            Item("ar36"),
            BorderVGroup(
                Item("correct_for_decay"),
                Item("decay_days"),
                Readonly("decay_factor_37"),
                Readonly("decay_factor_39"),
            ),
        )

        v = View(
            VGroup(
                UItem("calculate_button"),
                # HGroup(Item('age', editor=TextEditor(read_only=True)),
                #        Item('age_err', editor=TextEditor(read_only=True))),
                HGroup(Readonly("age"), Readonly("age_err")),
                isogrp,
            ),
            resizable=True,
            width=750,
        )
        return v


if __name__ == "__main__":
    ag = AgeCalculator()
    ag.configure_traits(kind="live")
# ============= EOF =============================================
