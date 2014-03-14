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
from traits.trait_types import Int, Str
from traits.traits import Property

#============= standard library imports ========================
#============= local library imports  ==========================



#============= EOF =============================================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import format_percent_error
from uncertainties import nominal_value, std_dev
from pychron.core.helpers.formatting import floatfmt, calc_percent_error

SIGMA_1 = u'\u00b11\u03c3'
TABLE_FONT = 'arial 11'

vwidth = Int(60)
ewidth = Int(50)
pwidth = Int(40)


class BaseTabularAdapter(TabularAdapter):
    default_bg_color = '#F7F6D0'
    font = TABLE_FONT


class DetectorRatioTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               (SIGMA_1, 'error'),
               ('Calc. IC', 'calc_ic'),
               ('ICFactor', 'ic_factor'),
               ('Ref. Ratio', 'ref_ratio'),

               ('Non IC Corrected', 'noncorrected_value'),
               (SIGMA_1, 'noncorrected_error'),
    ]
    calc_ic_text = Property

    noncorrected_value_text = Property
    noncorrected_error_text = Property

    def _get_calc_ic_text(self):
        return floatfmt(self.item.calc_ic)

    def _get_noncorrected_value_text(self):
        return floatfmt(self.item.noncorrected_value)

    def _get_noncorrected_error_text(self):
        return floatfmt(self.item.noncorrected_error)


class MeasurementTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'), ]
    name_width = Int(80)
    value_width = Int(80)


class ExtractionTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               ('Units', 'units')]

    name_width = Int(80)
    value_width = Int(90)
    units_width = Int(40)


class ComputedValueTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               (SIGMA_1, 'error'),
               ('%', 'percent_error'),

               ]
    name_width = Int(80)
    value_width = Int(120)
    units_width = Int(40)
    error_text=Property
    percent_error_text=Property
    value_text=Property

    def _get_value_text(self):
        if self.item.display_value:
            v=self.item.value
            return floatfmt(v, n=10, s=10)
        else:
            return ''

    def _get_error_text(self):
        v = self.item.error
        return floatfmt(v, 8)

    def _get_percent_error_text(self):
        e = self.item.error
        v = self.item.value

        return format_percent_error(v,e)

class IntermediateTabularAdapter(BaseTabularAdapter):
    columns = [('Iso.', 'name'),
               ('I','intercept'),
               (SIGMA_1,'intercept_error'),
               ('I-Bs', 'bs_corrected'),
               (SIGMA_1, 'bs_corrected_error'),
               ('%', 'bs_corrected_percent_error'),
               ('I-Bs-Bk', 'bs_bk_corrected'),
               (SIGMA_1, 'bs_bk_corrected_error'),
               ('%', 'bs_bk_corrected_percent_error'),

               ('S*D', 'disc_corrected'),
               (SIGMA_1, 'disc_corrected_error'),
               ('%', 'disc_corrected_percent_error'),

               ('IFC', 'interference_corrected'),
               (SIGMA_1, 'interference_corrected_error'),
               ('%', 'interference_corrected_percent_error')]

    intercept_text= Property
    intercept_error_text= Property
    intercept_tooltip=Str('Isotope regression t-zero (I)ntercept')

    bs_corrected_text = Property
    bs_corrected_error_text = Property
    bs_corrected_percent_error_text = Property
    bs_corrected_tooltip = Str('Baseline (Bs) corrected intercept')

    bs_bk_corrected_text = Property
    bs_bk_corrected_error_text = Property
    bs_bk_corrected_percent_error_text = Property
    bs_bk_corrected_tooltip = Str('Baseline (Bs) and Blank (Bk) corrected intercept. (S)ignal)')

    disc_corrected_text = Property
    disc_corrected_error_text = Property
    disc_corrected_percent_error_text = Property
    disc_corrected_tooltip = Str('(D)iscrimination corrected signal')

    interference_corrected_text = Property
    interference_corrected_error_text = Property
    interference_corrected_percent_error_text = Property
    interference_corrected_tooltip = Str('Interference corrected isotopic value')

    bs_corrected_width = Int(60)
    bs_corrected_error_width = Int(60)
    bs_corrected_percent_error_width = Int(60)

    bs_bk_corrected_width = Int(60)
    bs_bk_corrected_error_width = Int(60)
    bs_bk_corrected_percent_error_width = Int(60)

    disc_corrected_width = Int(60)
    disc_corrected_error_width = Int(60)
    disc_corrected_percent_error_width = Int(60)

    name_width = Int(40)
    intercept_width = Int(60)
    intercept_error_width = Int(60)

    name_width = Int(40)
    bs_corrected_width = Int(65)
    bs_corrected_error_width = Int(65)
    bs_corrected_percent_error_width = Int(65)

    bs_bk_corrected_width = Int(65)
    bs_bk_corrected_error_width = Int(65)
    bs_bk_corrected_percent_error_width = Int(65)

    disc_corrected_width = Int(65)
    disc_corrected_error_width = Int(65)
    disc_corrected_percent_error_width = Int(65)

    intensity_width = Int(65)
    intensity_error_width = Int(65)
    intensity_percent_error_width = Int(65)

    def _get_intercept_text(self):
        v = self.item.value
        return floatfmt(v, n=7)

    def _get_intercept_error_text(self):
        v = self.item.error
        return floatfmt(v, n=7)

    def _get_bs_corrected_text(self):
        v = self.item.get_baseline_corrected_value()
        return floatfmt(nominal_value(v), n=7)

    def _get_bs_corrected_error_text(self):
        v = self.item.get_baseline_corrected_value()
        return floatfmt(std_dev(v), n=7)

    def _get_bs_corrected_percent_error_text(self):
        v = self.item.get_baseline_corrected_value()
        return calc_percent_error(v.nominal_value, v.std_dev)

    #============================================================
    def _get_bs_bk_corrected_text(self):
        v = self.item.get_corrected_value()
        return floatfmt(nominal_value(v), n=7)

    def _get_bs_bk_corrected_error_text(self):
        v = self.item.get_corrected_value()
        return floatfmt(std_dev(v), n=7)

    def _get_bs_bk_corrected_percent_error_text(self):
        v = self.item.get_corrected_value()
        return calc_percent_error(v.nominal_value, v.std_dev)

    #============================================================
    def _get_disc_corrected_text(self):
        v = self.item.get_disc_corrected_value()
        return floatfmt(nominal_value(v), n=7)

    def _get_disc_corrected_error_text(self):
        v = self.item.get_disc_corrected_value()
        return floatfmt(std_dev(v), n=7)

    def _get_disc_corrected_percent_error_text(self):
        v = self.item.get_disc_corrected_value()
        return calc_percent_error(v.nominal_value, v.std_dev)

    #============================================================
    def _get_interference_corrected_text(self):
        v = self.item.get_interference_corrected_value()
        return floatfmt(nominal_value(v), n=7)

    def _get_interference_corrected_error_text(self):
        v = self.item.get_interference_corrected_value()
        return floatfmt(std_dev(v), n=7)

    def _get_interference_corrected_percent_error_text(self):
        v = self.item.get_interference_corrected_value()
        return calc_percent_error(v.nominal_value, v.std_dev)


class IsotopeTabularAdapter(BaseTabularAdapter):
    columns = [('Iso.', 'name'),
               ('Det.', 'detector'),
               ('Fit', 'fit_abbreviation'),

               ('Int.', 'value'),
               (SIGMA_1, 'error'),
               ('%', 'value_percent_error'),
               ('I. BsEr', 'include_baseline_error'),
               ('Fit', 'baseline_fit_abbreviation'),
               ('Base.', 'base_value'),
               (SIGMA_1, 'base_error'),
               ('%', 'baseline_percent_error'),
               ('Blank', 'blank_value'),
               (SIGMA_1, 'blank_error'),
               ('%', 'blank_percent_error'),
               ('IC', 'ic_factor'),
               ('Disc', 'discrimination'),
               ('Error Comp.', 'age_error_component')]

    value_tooltip = Str('Baseline, Blank, IC and/or Discrimination corrected')
    value_text = Property
    error_text = Property
    base_value_text = Property
    base_error_text = Property
    blank_value_text = Property
    blank_error_text = Property
    ic_factor_text = Property
    discrimination_text = Property
    include_baseline_error_text = Property

    value_percent_error_text = Property
    blank_percent_error_text = Property
    baseline_percent_error_text = Property
    age_error_component_text = Property

    name_width = Int(40)
    fit_abbreviation_width = Int(25)
    include_baseline_error_width = Int(40)
    baseline_fit_abbreviation_width = Int(25)
    detector_width = Int(40)

    value_width = vwidth
    error_width = ewidth

    base_value_width = vwidth
    base_error_width = ewidth
    blank_value_width = vwidth
    blank_error_width = ewidth

    value_percent_error_width = pwidth
    blank_percent_error_width = pwidth
    baseline_percent_error_width = pwidth

    ic_factor_width = Int(50)
    discrimination_width = Int(50)

    def _get_ic_factor_text(self):
        ic = self.item.ic_factor
        if ic is None:
            v = 0.0
        else:
            v = ic.nominal_value

        return floatfmt(v, n=4)

    def _get_discrimination_text(self):
        ic = self.item.discrimination
        if ic is None:
            v, e = 1.0, 0
        else:
            v, e = nominal_value(ic), std_dev(ic)

        return '{}+/-{}'.format(floatfmt(v, n=4), floatfmt(e))

    def _get_value_text(self, *args, **kw):
        v = self.item.get_intensity()
        return floatfmt(v.nominal_value, n=6)

    def _get_error_text(self, *args, **kw):
        v = self.item.get_intensity()
        return floatfmt(v.std_dev, n=6)

    def _get_base_value_text(self, *args, **kw):
        return floatfmt(self.item.baseline.value, n=6)

    def _get_base_error_text(self, *args, **kw):
        return floatfmt(self.item.baseline.error, n=6)

    def _get_blank_value_text(self, *args, **kw):
        return floatfmt(self.item.blank.value, n=6)

    def _get_blank_error_text(self, *args, **kw):
        return floatfmt(self.item.blank.error, n=6)

    def _get_baseline_percent_error_text(self, *args):
        b = self.item.baseline
        return format_percent_error(b.value, b.error)

    def _get_blank_percent_error_text(self, *args):
        b = self.item.blank
        return format_percent_error(b.value, b.error)

    def _get_value_percent_error_text(self, *args):
        cv = self.item.get_corrected_value()
        return format_percent_error(cv.nominal_value, cv.std_dev)

    def _get_age_error_component_text(self):
        return floatfmt(self.item.age_error_component, n=1)

    def _get_include_baseline_error_text(self):
        return 'Yes' if self.item.include_baseline_error else 'No'