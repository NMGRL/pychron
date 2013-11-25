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
from traits.trait_types import Int
from traits.traits import Property

#============= standard library imports ========================
#============= local library imports  ==========================



#============= EOF =============================================
from traitsui.tabular_adapter import TabularAdapter
from pychron.helpers.formatting import floatfmt, calc_percent_error

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


class CompuatedValueTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               (SIGMA_1, 'error'),
    ]
    name_width = Int(80)
    value_width = Int(80)
    units_width = Int(40)


class IsotopeTabularAdapter(BaseTabularAdapter):
    columns = [('Iso.', 'name'),
               ('Det.', 'detector'),
               ('Fit', 'fit_abbreviation'),
               ('Int.', 'value'),
               (SIGMA_1, 'error'),
               ('%', 'value_percent_error'),
               ('Fit', 'baseline_fit_abbreviation'),
               ('Base.', 'base_value'),
               (SIGMA_1, 'base_error'),
               ('%', 'baseline_percent_error'),
               ('Blank', 'blank_value'),
               (SIGMA_1, 'blank_error'),
               ('%', 'blank_percent_error'),
               ('IC', 'ic_factor'),
               ('Error Comp.', 'age_error_component')]

    value_text = Property
    error_text = Property
    base_value_text = Property
    base_error_text = Property
    blank_value_text = Property
    blank_error_text = Property
    ic_factor_text=Property

    value_percent_error_text = Property
    blank_percent_error_text = Property
    baseline_percent_error_text = Property
    age_error_component_text = Property

    name_width = Int(40)
    fit_abbreviation_width = Int(25)
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

    def _get_ic_factor_text(self):
        ic = self.item.ic_factor
        return floatfmt(ic.nominal_value, n=2)

    def _get_value_text(self, *args, **kw):
        v = self.item.get_corrected_value()
        return floatfmt(v.nominal_value)

    def _get_error_text(self, *args, **kw):
        v = self.item.get_corrected_value()
        return floatfmt(v.std_dev)

    def _get_base_value_text(self, *args, **kw):
        return floatfmt(self.item.baseline.value)

    def _get_base_error_text(self, *args, **kw):
        return floatfmt(self.item.baseline.error)

    def _get_blank_value_text(self, *args, **kw):
        return floatfmt(self.item.blank.value)

    def _get_blank_error_text(self, *args, **kw):
        return floatfmt(self.item.blank.error)

    def _get_baseline_percent_error_text(self, *args):
        b = self.item.baseline
        return calc_percent_error(b.value, b.error)

    def _get_blank_percent_error_text(self, *args):
        b = self.item.blank
        return calc_percent_error(b.value, b.error)

    def _get_value_percent_error_text(self, *args):
        cv = self.item.get_corrected_value()
        return calc_percent_error(cv.nominal_value, cv.std_dev)

    def _get_age_error_component_text(self):
        return floatfmt(self.item.age_error_component, n=1)