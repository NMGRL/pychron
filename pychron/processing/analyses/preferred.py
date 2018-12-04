# ===============================================================================
# Copyright 2018 ross
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

from traits.api import HasTraits, Str, List, Float, Event
from traitsui.api import EnumEditor, TableEditor, ObjectColumn, UItem, VGroup
from uncertainties import ufloat

from pychron.core.helpers.formatting import floatfmt
from pychron.pychron_constants import MSEM, ERROR_TYPES, SUBGROUPINGS, SD, AGE_SUBGROUPINGS, WEIGHTED_MEAN, \
    PLATEAU_ELSE_WEIGHTED_MEAN, WEIGHTINGS


class PreferredValue(HasTraits):
    attr = Str
    error_kind = Str(MSEM)
    error_kinds = List(ERROR_TYPES)
    kind = Str(WEIGHTED_MEAN)
    kinds = List(SUBGROUPINGS)
    computed_kind = Str
    value = Float
    error = Float

    weighting = Str
    weightings = List(WEIGHTINGS)
    dirty = Event

    @property
    def uvalue(self):
        return ufloat(self.value, self.error)

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in ('attr', 'error_kind', 'kind', 'value', 'error', 'weighting')}

    def _kind_changed(self, new):
        if new in ('Plateau Integrated', 'Valid Integrated', 'Total Integrated', 'Arithmetic Mean'):
            self.error_kinds = [SD, ]
            self.error_kind = SD
        else:
            self.error_kinds = ERROR_TYPES


class AgePreferredValue(PreferredValue):
    kind = Str(PLATEAU_ELSE_WEIGHTED_MEAN)
    kinds = List(AGE_SUBGROUPINGS)


def make_preferred_values():
    preferred_values = [PreferredValue(name=name, attr=attr) for name, attr in (
        ('K/Ca', 'kca'),
        ('K/Cl', 'kcl'),
        ('%40Ar*', 'rad40_percent'),
        ('Mol 39K', 'moles_k39'),
        ('Signal 39K', 'signal_k39'))]
    preferred_values.insert(0, AgePreferredValue(name='Age', attr='age'))
    return preferred_values


cols = [ObjectColumn(name='name', label='Name', editable=False),
        ObjectColumn(name='kind', label='Kind', editor=EnumEditor(name='kinds')),
        ObjectColumn(name='error_kind',
                     editor=EnumEditor(name='error_kinds'),
                     label='Error Kind'),
        ObjectColumn(name='value', label='Value', editable=False,
                     format_func=lambda x: floatfmt(x, use_scientific=True)),
        ObjectColumn(name='error', label='Error', editable=False,
                     format_func=lambda x: floatfmt(x, n=7, use_scientific=True)),
        ObjectColumn(name='weighting',
                     editor=EnumEditor(name='weightings'))]

preferred_item = UItem('preferred_values', editor=TableEditor(sortable=False, columns=cols))


def get_preferred_grp(**kw):

    return VGroup(preferred_item, **kw)


class Preferred(HasTraits):
    preferred_values = List

    # due to a potential? MRO issue include... must be defined by subclasses
    # AnalysisGroup defines include... but InterpretedAgeGroup inherits StepHeatAnalysisGroup and Preferred
#    include_j_err_in_individual_analyses = Bool(False)
#    include_j_err_in_mean = Bool(True)

    def __init__(self, *args, **kw):
        super(Preferred, self).__init__(*args, **kw)
        self.preferred_values = make_preferred_values()

    def _get_pv(self, attr):
        return next((pv for pv in self.preferred_values if pv.attr == attr))

# ============= EOF =============================================
