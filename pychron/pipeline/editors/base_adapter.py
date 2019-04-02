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
from __future__ import absolute_import

from traits.api import HasTraits, Int, Str, Property, Any
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import std_dev, nominal_value

from pychron.core.helpers.formatting import floatfmt


# ============= standard library imports ========================
# ============= local library imports  ==========================
class TableBlank(HasTraits):
    analysis = Any

    def __getattr__(self, attr):
        return getattr(self.analysis, attr)


class TableSeparator(HasTraits):
    name = Str

    def __getattr__(self, attr):
        return ''


def swidth(v=60):
    return Int(v)


def ewidth(v=50):
    return Int(v)


class BaseAdapter(TabularAdapter):
    blank_column_text = Str('')

    labnumber_width = Int(60)
    aliquot_step_str_width = Int(30)
    extract_value_width = Int(40)
    moles_Ar40_width = Int(50)

    ar40_width = swidth()
    ar39_width = swidth()
    ar38_width = swidth()
    ar37_width = swidth()
    ar36_width = swidth()

    ar40_err_width = ewidth()
    ar39_err_width = ewidth()
    ar38_err_width = ewidth()
    ar37_err_width = ewidth()
    ar36_err_width = ewidth(65)

    radiogenic_yield_width = Int(60)
    age_width = swidth()
    age_err_width = ewidth()
    R_width = Int(70)
    R_width = Int(70)

    font = 'Arial 10'

    sensitivity_scalar = 1e9

    def _get_value(self, attr, n=3, **kw):
        return self._get_attribute_value(nominal_value, attr, n, **kw)

    def _get_error(self, attr, n=3, **kw):
        return self._get_attribute_value(std_dev, attr, n, **kw)

    def _get_attribute_value(self, func, attr, n, **kw):
        v = ''
        item = self.item
        if hasattr(item, 'isotopes'):
            # print attr in item.isotopes
            if attr in item.isotopes:
                v = item.isotopes[attr].get_intensity()
                v = floatfmt(func(v), n=n, **kw)
            elif hasattr(item, attr):
                v = getattr(self.item, attr)
                if v:
                    v = floatfmt(func(v), n=n, **kw)
        elif hasattr(item, attr):
            v = getattr(self.item, attr)
            if v:
                v = floatfmt(func(v), n=n, **kw)
        return v


class BaseGroupAdapter(BaseAdapter):
    columns = [
        ('Identifier', 'identifier'),
        ('Sample', 'sample'),
        ('N', 'nanalyses'),
        ('Wtd. Age', 'weighted_age'),
        ('S.E', 'age_se'),
        ('MSWD', 'mswd'),
        ('Wtd. K/Ca', 'weighted_kca_error'),
        ('S.E', 'weighted_kca'),
        ('', 'blank_column')
    ]

    nanalyses_width = Int(40)
    sample_width = Int(75)
    identifier_width = Int(75)
    mswd_width = Int(75)
    weighted_age_width = Int(75)
    weighted_kca_width = Int(75)
    weighted_kca_error_width = Int(75)

    arith_age_width = Int(75)
    age_se_width = Int(75)

    weighted_age_text = Property
    age_se_text = Property
    mswd_text = Property
    weighted_kca_text = Property
    weighted_kca_error_text = Property

    font = 'Arial 9'

    def get_bg_color(self, obj, trait, row, column):
        return 'white'

    def _get_weighted_age_text(self):
        return self._get_value('weighted_age')

    def _get_age_se_text(self):
        return self._get_error('weighted_age')

    def _get_weighted_kca_text(self):
        return self._get_value('weighted_kca')

    def _get_weighted_kca_error_text(self):
        return self._get_error('weighted_kca')

    def _get_mswd_text(self):
        return floatfmt(self.item.mswd, 2)

# ============= EOF =============================================
