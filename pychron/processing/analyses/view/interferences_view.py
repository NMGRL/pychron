# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Str, Float, List, Property
from traitsui.api import View, Item, UItem, TabularEditor, VGroup, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev
from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, PLUSMINUS_PERCENT

MAPPING = {'k4039': ('(Ar40/Ar39)K'),
           'k3839': ('(Ar38/Ar39)K'),
           'k3739': ('(Ar37/Ar39)K'),
           'ca3937': ('(Ar39/Ar37)Ca'),
           'ca3837': ('(Ar38/Ar37)Ca'),
           'ca3637': ('(Ar36/Ar37)Ca'),
           'cl3638': ('(Ar36/Ar38)Cl')}


class Interference(HasTraits):
    name = Str
    value = Float
    error = Float


class InterferenceAdapter(TabularAdapter):
    columns = [('Correction', 'name'),
               ('Value', 'value'), (PLUSMINUS_ONE_SIGMA, 'error'),
               (PLUSMINUS_PERCENT, 'percent_error')]

    value_text = Property
    error_text = Property
    percent_error_text = Property
    font = '10'

    def _get_value_text(self):
        return floatfmt(self.item.value)

    def _get_error_text(self):
        return floatfmt(self.item.error)

    def _get_percent_error_text(self):
        return format_percent_error(self.item.value, self.item.error)


class InterferencesView(HasTraits):
    interferences = List
    productions = List
    name = 'Interferences'

    def __init__(self, an, *args, **kw):
        super(InterferencesView, self).__init__(*args, **kw)
        self._load(an)

    def _load(self, an):
        # print an.interference_corrections
        # print an.production_name
        # print an.production_ratios
        self.pr_name = an.production_name
        a = []

        for k, v in sorted(an.interference_corrections.iteritems(), key=lambda x: x[0]):
            if k in MAPPING:
                k = MAPPING[k]

            a.append(Interference(name=k, value=v.nominal_value,
                                  error=v.std_dev))
        self.interferences = a

        p = []
        for k, v in an.production_ratios.iteritems():
            p.append(Interference(name=k.replace('_', '/'),
                                  value=nominal_value(v),
                                  error=std_dev(v)))
        self.productions = p

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('pr_name',
                        label='Name',
                        style='readonly')),
            UItem('interferences',
                  editor=TabularEditor(adapter=InterferenceAdapter(),
                                       editable=False)),
            UItem('productions', editor=TabularEditor(adapter=InterferenceAdapter(),
                                                      editable=False))))
        return v

# ============= EOF =============================================

