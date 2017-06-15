from traits.trait_types import Date as TDate, Long, Str, Float, Int, Bool
from traits.traits import Property
from traitsui.group import HGroup
from traitsui.item import Item
from traitsui.view import View

from pychron.core.helpers.formatting import floatfmt
from pychron.processing.analyses.analysis import IdeogramPlotable

__author__ = 'ross'


class InterpretedAge(IdeogramPlotable):
    create_date = TDate
    id = Long

    sample = Str
    lithology = Str
    identifier = Str
    material = Str
    irradiation = Str

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
    include_j_error_in_individual_analyses = Bool

    display_age = Property
    display_age_err = Property
    display_age_units = Str('Ma')

    def _value_string(self, t):
        if t == 'uF':
            a, e = self.F, self.F_err
        elif t == 'uage':
            a, e = self.uage.nominal_value, self.uage.std_dev
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