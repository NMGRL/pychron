# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from pyface.action.menu_manager import MenuManager
from traits.trait_types import Int, Str
from traits.traits import Property
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.formatting import format_percent_error
from pychron.pychron_constants import NULL_STR

SIGMA_1 = "\u00b11\u03c3"
TABLE_FONT = "arial 11"

vwidth = Int(80)
ewidth = Int(70)
eewidth = Int(80)
pwidth = Int(50)


def sigmaf(s):
    return "{}({})".format(SIGMA_1, s)


def handle_error(func):
    def wrapper(self_args):
        try:
            return func(self_args)
        except ValueError:
            return ""

    return wrapper


class BaseTabularAdapter(TabularAdapter):
    default_bg_color = "#F7F6D0"
    font = TABLE_FONT


class DetectorRatioTabularAdapter(BaseTabularAdapter):
    columns = [
        ("Name", "name"),
        ("Value", "value"),
        (SIGMA_1, "error"),
        ("%", "perror"),
        ("Calc. IC", "calc_ic"),
        ("ICFactor", "ic_factor"),
        ("Ref. Ratio", "ref_ratio"),
        ("Non IC Corrected", "noncorrected_value"),
        (SIGMA_1, "noncorrected_error"),
    ]

    value_text = Property
    error_text = Property
    calc_ic_text = Property
    ic_factor_text = Property
    ref_ratio_text = Property
    noncorrected_value_text = Property
    noncorrected_error_text = Property
    perror_text = Property

    def _get_perror_text(self):
        try:
            return floatfmt(float(self.item.error) / float(self.item.value) * 100)
        except (ZeroDivisionError, ValueError, TypeError):
            return "nan"

    def _get_value_text(self):
        return floatfmt(self.item.value)

    def _get_error_text(self):
        return floatfmt(self.item.error)

    def _get_attr_text(self, attr):
        try:
            return floatfmt(getattr(self.item, attr))
        except AttributeError:
            return NULL_STR

    def _get_ic_factor_text(self):
        return self._get_attr_text("ic_factor")

    def _get_ref_ratio_text(self):
        return self._get_attr_text("ref_ratio")

    def _get_calc_ic_text(self):
        return self._get_attr_text("calc_ic")

    def _get_noncorrected_value_text(self):
        return self._get_attr_text("noncorrected_value")

    def _get_noncorrected_error_text(self):
        return self._get_attr_text("noncorrected_error")


class MeasurementTabularAdapter(BaseTabularAdapter):
    columns = [("Name", "name"), ("Value", "value"), ("Units", "units")]
    name_width = Int(120)
    value_width = Int(250)
    units_width = Int(40)


class ExtractionTabularAdapter(BaseTabularAdapter):
    columns = [("Name", "name"), ("Value", "value"), ("Units", "units")]

    name_width = Int(120)
    value_width = Int(250)
    units_width = Int(40)


class ComputedValueTabularAdapter(BaseTabularAdapter):
    columns = [
        ("Name", "name"),
        ("Value", "value"),
        (SIGMA_1, "error"),
        ("%", "percent_error"),
    ]

    name_width = Int(80)
    value_width = Int(120)
    units_width = Int(40)
    error_width = Int(60)
    error_text = Property
    percent_error_text = Property
    value_text = Property

    def _get_value_text(self):
        item = self.item
        if item.display_value:
            v = item.value
            n = item.sig_figs
            return floatfmt(v, n=n, s=n)
        else:
            return ""

    def _get_error_text(self):
        item = self.item
        v = item.error
        n = item.sig_figs
        return floatfmt(v, n)

    def _get_percent_error_text(self):
        e = self.item.error
        v = self.item.value

        return format_percent_error(v, e)


class IntermediateTabularAdapter(BaseTabularAdapter, ConfigurableMixin):
    all_columns = [
        ("Name", "name"),
        ("I", "intercept"),
        (SIGMA_1, "intercept_error"),
        ("%", "intercept_percent_error"),
        ("I-Bs", "bs_corrected"),
        (sigmaf("I-Bs"), "bs_corrected_error"),
        ("%(I-Bs)", "bs_corrected_percent_error"),
        ("I-Bs-Bk", "bs_bk_corrected"),
        (sigmaf("I-Bs-Bk"), "bs_bk_corrected_error"),
        ("%(I-Bs-Bk)", "bs_bk_corrected_percent_error"),
        ("S*D", "disc_corrected"),
        (sigmaf("S*D"), "disc_corrected_error"),
        ("%(S*D)", "disc_corrected_percent_error"),
        ("S*IC", "ic_corrected"),
        (sigmaf("S*IC"), "ic_corrected_error"),
        ("%(S*IC)", "ic_corrected_percent_error"),
        ("S*IC*DecayFactor", "ic_decay_corrected"),
        (sigmaf("S*IC*DecayFactor"), "ic_decay_corrected_error"),
        ("%(S*IC*DecayFactor)", "ic_decay_corrected_percent_error"),
        ("IFC", "interference_corrected"),
        (sigmaf("IFC"), "interference_corrected_error"),
        ("%(IFC)", "interference_corrected_percent_error"),
    ]
    columns = [("Name", "name")]

    intercept_text = Property
    intercept_error_text = Property
    intercept_percent_error_text = Property
    intercept_tooltip = Str("Isotope regression t-zero (I)ntercept")

    bs_corrected_text = Property
    bs_corrected_error_text = Property
    bs_corrected_percent_error_text = Property
    bs_corrected_tooltip = Str("Baseline (Bs) corrected intercept")

    bs_bk_corrected_text = Property
    bs_bk_corrected_error_text = Property
    bs_bk_corrected_percent_error_text = Property
    bs_bk_corrected_tooltip = Str(
        "Baseline (Bs) and Blank (Bk) corrected intercept. (S)ignal)"
    )

    disc_corrected_text = Property
    disc_corrected_error_text = Property
    disc_corrected_percent_error_text = Property
    disc_corrected_tooltip = Str("(D)iscrimination corrected signal")

    ic_corrected_text = Property
    ic_corrected_error_text = Property
    ic_corrected_percent_error_text = Property
    ic_corrected_tooltip = Str("(IC) Detector intercalibration corrected signal")

    ic_decay_corrected_text = Property
    ic_decay_corrected_error_text = Property
    ic_decay_corrected_percent_error_text = Property
    ic_decay_corrected_tooltip = Str(
        "(IC) Detector intercalibration corrected signal and decay corrected"
    )

    interference_corrected_text = Property
    interference_corrected_error_text = Property
    interference_corrected_percent_error_text = Property
    interference_corrected_tooltip = Str("Interference corrected isotopic value")

    # bs_corrected_width = Int(60)
    # bs_corrected_error_width = eewidth
    # bs_corrected_percent_error_width = pwidth

    # bs_bk_corrected_width = Int(60)
    # bs_bk_corrected_error_width = eewidth
    # bs_bk_corrected_percent_error_width = pwidth

    # disc_corrected_width = Int(60)
    # disc_corrected_error_width = Int(60)
    # disc_corrected_percent_error_width = Int(60)

    name_width = Int(50)
    intercept_width = vwidth
    intercept_error_width = eewidth
    intercept_percent_error_width = pwidth

    bs_corrected_width = Int(65)
    bs_corrected_error_width = eewidth
    bs_corrected_percent_error_width = pwidth

    bs_bk_corrected_width = Int(65)
    bs_bk_corrected_error_width = eewidth
    bs_bk_corrected_percent_error_width = pwidth

    disc_corrected_width = Int(65)
    disc_corrected_error_width = eewidth
    disc_corrected_percent_error_width = pwidth

    intensity_width = Int(65)
    intensity_error_width = eewidth
    intensity_percent_error_width = pwidth

    sig_figs = Int(7)

    def _value(self, v):
        return floatfmt(nominal_value(v), n=self.sig_figs)

    def _error(self, v):
        return floatfmt(std_dev(v), n=self.sig_figs)

    @handle_error
    def _get_intercept_text(self):
        v = self.item.value
        return self._value(v)

    @handle_error
    def _get_intercept_error_text(self):
        v = self.item.error
        return self._value(v)

    @handle_error
    def _get_intercept_percent_error_text(self):
        v = self.item.uvalue
        return format_percent_error(nominal_value(v), std_dev(v))

    @handle_error
    def _get_bs_corrected_text(self):
        v = self.item.get_baseline_corrected_value()
        return self._value(v)

    @handle_error
    def _get_bs_corrected_error_text(self):
        v = self.item.get_baseline_corrected_value()
        return self._error(v)

    @handle_error
    def _get_bs_corrected_percent_error_text(self):
        v = self.item.get_baseline_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))

    # ============================================================
    @handle_error
    def _get_bs_bk_corrected_text(self):
        v = self.item.get_non_detector_corrected_value()
        return self._value(v)

    @handle_error
    def _get_bs_bk_corrected_error_text(self):
        v = self.item.get_non_detector_corrected_value()
        return self._error(v)

    @handle_error
    def _get_bs_bk_corrected_percent_error_text(self):
        v = self.item.get_non_detector_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))

    # ============================================================
    @handle_error
    def _get_disc_corrected_text(self):
        v = self.item.get_disc_corrected_value()
        return self._value(v)

    @handle_error
    def _get_disc_corrected_error_text(self):
        v = self.item.get_disc_corrected_value()
        return self._error(v)

    @handle_error
    def _get_disc_corrected_percent_error_text(self):
        v = self.item.get_disc_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))

    # ============================================================
    @handle_error
    def _get_ic_corrected_text(self):
        v = self.item.get_ic_corrected_value()
        return self._value(v)

    @handle_error
    def _get_ic_corrected_error_text(self):
        v = self.item.get_ic_corrected_value()
        return self._error(v)

    @handle_error
    def _get_ic_corrected_percent_error_text(self):
        v = self.item.get_ic_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))

    # ============================================================
    @handle_error
    def _get_ic_decay_corrected_text(self):
        v = self.item.get_ic_decay_corrected_value()
        return self._value(v)

    @handle_error
    def _get_ic_decay_corrected_error_text(self):
        v = self.item.get_ic_decay_corrected_value()
        return self._error(v)

    @handle_error
    def _get_ic_decay_corrected_percent_error_text(self):
        v = self.item.get_ic_decay_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))

    # ============================================================
    @handle_error
    def _get_interference_corrected_text(self):
        v = self.item.get_interference_corrected_value()
        return self._value(v)

    @handle_error
    def _get_interference_corrected_error_text(self):
        v = self.item.get_interference_corrected_value()
        return self._error(v)

    @handle_error
    def _get_interference_corrected_percent_error_text(self):
        v = self.item.get_interference_corrected_value()
        return format_percent_error(nominal_value(v), std_dev(v))


class IsotopeTabularAdapter(BaseTabularAdapter, ConfigurableMixin):
    all_columns = [
        ("Name", "name"),
        ("Det.", "detector"),
        ("Det. ID", "detector_serial_id"),
        ("Fit", "fit_abbreviation"),
        ("Error", "error_type"),
        ("Iso", "value"),
        (SIGMA_1, "error"),
        ("%", "value_percent_error"),
        ("I. BsEr", "include_baseline_error"),
        ("Fit(Bs)", "baseline_fit_abbreviation"),
        ("Bs", "base_value"),
        (sigmaf("Bs"), "base_error"),
        ("%(Bs)", "baseline_percent_error"),
        ("Bk", "blank_value"),
        (sigmaf("Bk"), "blank_error"),
        ("%(Bk)", "blank_percent_error"),
        ("Bk Source", "blank_source"),
        ("IC", "ic_factor"),
        (sigmaf("IC"), "ic_factor_error"),
        ("Disc", "discrimination"),
        ("Error Comp.", "age_error_component"),
    ]
    columns = [
        ("Name", "name"),
        ("Det.", "detector"),
        ("Fit", "fit_abbreviation"),
        ("Error", "error_type"),
        ("Iso", "value"),
        (SIGMA_1, "error"),
        ("%", "value_percent_error"),
        # ('I. BsEr', 'include_baseline_error'),
        ("Fit(Bs)", "baseline_fit_abbreviation"),
        ("Bs", "base_value"),
        (sigmaf("Bs"), "base_error"),
        ("%(Bs)", "baseline_percent_error"),
        ("Bk", "blank_value"),
        (sigmaf("Bk"), "blank_error"),
        ("%(Bk)", "blank_percent_error"),
        ("Bk Source", "blank_source"),
        ("IC", "ic_factor"),
    ]

    value_tooltip = Str("Baseline, Blank, IC and/or Discrimination corrected")
    value_text = Property
    error_text = Property
    base_value_text = Property
    base_error_text = Property
    blank_value_text = Property
    blank_error_text = Property
    ic_factor_text = Property
    ic_factor_error_text = Property
    discrimination_text = Property
    include_baseline_error_text = Property

    value_percent_error_text = Property
    blank_percent_error_text = Property
    baseline_percent_error_text = Property
    age_error_component_text = Property

    name_width = Int(50)
    fit_abbreviation_width = Int(40)
    error_type_width = Int(60)
    include_baseline_error_width = Int(40)
    baseline_fit_abbreviation_width = Int(60)
    detector_width = Int(60)

    value_width = vwidth
    error_width = ewidth

    base_value_width = vwidth
    base_error_width = ewidth
    blank_value_width = vwidth
    blank_error_width = ewidth

    value_percent_error_width = pwidth
    blank_percent_error_width = pwidth
    baseline_percent_error_width = pwidth

    ic_factor_width = Int(60)
    ic_factor_error_width = Int(70)
    discrimination_width = Int(50)
    sig_figs = Int(4)

    def get_menu(self, obj, trait, row, column):
        return MenuManager(
            Action(name="Show Isotope Evolution", action="show_isotope_evolution"),
            Action(
                name="Show Isotope Evolution w/Equilibration",
                action="show_isotope_evolution_with_sniff",
            ),
            Action(
                name="Show Isotope Evolution w/Baseline",
                action="show_isotope_evolution_with_baseline",
            ),
            Action(name="Show Baseline", action="show_baseline"),
            Action(name="Show Equilibration", action="show_sniff"),
            Action(name="Show All", action="show_all"),
            Action(name="Show Inspection", action="show_inspection"),
            Action(name="Show Residuals", action="show_residuals"),
            Action(
                name="Show Equilibration Inspector",
                action="show_equilibration_inspector",
            ),
        )

    def _get_ic_factor_text(self):
        ic = self.item.ic_factor
        if ic is None:
            v = 0.0
        else:
            v = nominal_value(ic)

        return floatfmt(v, n=self.sig_figs)

    def _get_ic_factor_error_text(self):
        ic = self.item.ic_factor
        if ic is None:
            v = 0.0
        else:
            v = std_dev(ic)
        return floatfmt(v, n=self.sig_figs)

    def _get_discrimination_text(self):
        ic = self.item.discrimination
        if ic is None:
            v, e = 1.0, 0
        else:
            v, e = nominal_value(ic), std_dev(ic)

        return "{}+/-{}".format(
            floatfmt(v, n=self.sig_figs), floatfmt(e, n=self.sig_figs)
        )

    def _get_value_text(self, *args, **kw):
        v = self.item.get_intensity()
        return self._format(self.item, nominal_value(v), "value")

    def _get_error_text(self, *args, **kw):
        v = self.item.get_intensity()
        return self._format(self.item, std_dev(v), "error")

    def _format(self, item, v, v_or_e, n=None):
        if n is None:
            n = self.sig_figs

        if isinstance(item, str):
            item = getattr(self.item, item)

        if isinstance(v, str):
            v = getattr(item, v)

        t = floatfmt(v, n=n)
        if getattr(item, "use_manual_{}".format(v_or_e)):
            t = "#{}".format(t)
        return t

    def _get_base_value_text(self):
        return self._format("baseline", "value", "value")

    def _get_base_error_text(self):
        return self._format("baseline", "error", "error")

    @handle_error
    def _get_blank_value_text(self):
        return self._format("blank", "value", "value")

    @handle_error
    def _get_blank_error_text(self):
        return self._format("blank", "error", "error")

    @handle_error
    def _get_baseline_percent_error_text(self):
        b = self.item.baseline
        return format_percent_error(b.value, b.error)

    def _get_blank_percent_error_text(self):
        b = self.item.blank
        return format_percent_error(b.value, b.error)

    @handle_error
    def _get_value_percent_error_text(self):
        cv = self.item.get_non_detector_corrected_value()
        return format_percent_error(cv.nominal_value, cv.std_dev)

    def _get_age_error_component_text(self):
        return floatfmt(self.item.age_error_component, n=2)

    def _get_include_baseline_error_text(self):
        return "Yes" if self.item.include_baseline_error else "No"


# ============= EOF =============================================
