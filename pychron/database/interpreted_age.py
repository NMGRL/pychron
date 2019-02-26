# ===============================================================================
# Copyright 2015 Jake Ross
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
import uuid

from traits.trait_types import Date as TDate, Long, Str, Float, Int, Bool
from traits.traits import Property
from traitsui.group import HGroup
from traitsui.item import Item
from traitsui.view import View
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.processing.analyses.analysis import IdeogramPlotable


class InterpretedAge(IdeogramPlotable):
    create_date = TDate
    id = Long

    sample = Str
    lithology = Str
    identifier = Str
    material = Str
    irradiation = Str
    project = Str

    age = Float
    age_err = Float
    kca = Float
    kca_err = Float

    age_kind = Str
    kca_kind = Str
    mswd = Float
    nanalyses = Int

    age_error_kind = Str
    include_j_error_in_mean = Bool
    include_j_error_in_plateau = Bool
    include_j_position_error = Bool
    # include_j_error_in_individual_analyses = Bool

    display_age = Property
    display_age_err = Property
    display_age_units = Str('Ma')

    # reference = Str
    # rlocation = Str  # location of sample within unit
    # lat_long = Str

    uuid = Str

    def __init__(self, *args, **kw):
        super(InterpretedAge, self).__init__(*args, **kw)
        self.uuid = str(uuid.uuid4())

    def _value_string(self, t):
        if t == 'uF':
            a, e = self.f, self.f_err
        elif t == 'uage':
            a, e = nominal_value(self.uage), std_dev(self.uage)
        return a, e

    def _get_display_age(self):
        a = self.age
        return self._scale_age(a)

    def _get_display_age_err(self):
        e = self.age_err
        return self._scale_age(e)

    def _scale_age(self, a):
        if self.display_age_units == 'ka':
            a *= 1000
        elif self.display_age_units == 'Ga':
            a *= 0.001

        return a


interpreted_age_view = View(HGroup(Item('age_kind',
                                        style='readonly', show_label=False),
                                   Item('display_age', format_func=lambda x: floatfmt(x, 3),
                                        label='Age',
                                        style='readonly'),
                                   Item('display_age_err',
                                        label=u'\u00b11\u03c3',
                                        format_func=lambda x: floatfmt(x, 4),
                                        style='readonly'),
                                   Item('display_age_units',
                                        style='readonly', show_label=False),
                                   Item('mswd',
                                        format_func=lambda x: floatfmt(x, 2),
                                        style='readonly', label='MSWD')))

# ============= EOF =============================================
