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
from traits.api import Property, Int, Str
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.formatting import floatfmt

# ============= standard library imports ========================
# ============= local library imports  ==========================
class SummaryTabularAdapter(TabularAdapter):
    columns = [
               ('Sample', 'sample'),
               ('L#', 'identifier'),
               ('Irradiation', 'irradiation'),
               ('Material', 'material'),
               ('type', 'age_kind'),
               ('N', 'nanalyses'),
               ('MSWD', 'mswd'),
               ('K/Ca', 'kca'),
               (u'\u00b1 1\u03c3', 'kca_error'),
               ('Age', 'age'),
               (u'\u00b1 1\u03c3', 'age_error'),
               ('', 'blank')

               ]

    blank_text = Str('')
    sample_width = Int(100)
    identifier_width = Int(60)
    irradiation_width = Int(90)
    material_width = Int(100)
    age_kind_width = Int(115)
    nanalyses_width = Int(25)

    mswd_width = Int(75)
    kca_width = Int(75)
    kca_error_width = Int(75)
    age_width = Int(75)
    age_error_width = Int(75)
    blank_width = Int(25)

    mswd_text = Property
    kca_text = Property
    kca_error_text = Property
    age_text = Property
    age_error_text = Property

    font = 'arial 10'
    def _get_mswd_text(self):
        return floatfmt(self.item.mswd)

    def _get_kca_text(self):
        return floatfmt(self.item.weighted_kca.nominal_value, n=1)

    def _get_kca_error_text(self):
        return floatfmt(self.item.weighted_kca.std_dev, n=2)

    def _get_age_text(self):
        return floatfmt(self.item.weighted_age.nominal_value, n=5)

    def _get_age_error_text(self):
        return floatfmt(self.item.weighted_age.std_dev, n=6)

    def set_widths(self, ws):
        for (_, ai), wi in zip(self.columns, ws):
            attr = '{}_width'.format(ai)
            if hasattr(self, attr):
                setattr(self, attr, wi)


# ============= EOF =============================================
