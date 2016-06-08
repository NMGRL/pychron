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
from traits.api import Property, Instance, List, Either, Int, Float, HasTraits, \
    Str, Dict, Bool
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.core.helpers.formatting import floatfmt
from pychron.mass_spec.mass_spec_recaller import MassSpecRecaller
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA

DIFF_TOLERANCE = 1e-8


class ValueTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Pychron', 'lvalue'),
               ('Diff', 'diff'),
               ('MassSpec', 'rvalue'),
               ('% Dff', 'percent_diff')]

    lvalue_width = Int(100)
    diff_width = Int(100)
    rvalue_width = Int(100)
    # name_width = Int(100)
    name_width = Int(120)

    # name_text = Property
    lvalue_text = Property
    diff_text = Property
    rvalue_text = Property
    percent_diff_text = Property

    font = '12'
    use_bg_color = Bool(True)

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if self.use_bg_color:
            v = self.item.diff
            if abs(v) > 1e-8:
                color = '#FFCCCC'
        return color

    # def _get_name_text(self):
    #     return '<b>{}</b'.format(self.item.name)

    def _get_percent_diff_text(self):
        v = self.item.percent_diff
        return self._get_value_text(v, n=2)

    def _get_lvalue_text(self):
        v = self.item.lvalue
        return self._get_value_text(v)

    def _get_rvalue_text(self):
        v = self.item.rvalue
        return self._get_value_text(v)

    def _get_value_text(self, v, n=8):
        if isinstance(v, float):
            v = floatfmt(v, n=n)
        return v

    def _get_diff_text(self):
        v = self.item.diff
        if isinstance(v, float):
            if abs(v) < DIFF_TOLERANCE:
                v = ''
            else:
                v = floatfmt(v, n=8)
        elif isinstance(v, bool):
            v = '---' if v else ''

        if not v:
            v = ''

        return v


class Value(HasTraits):
    name = Str
    lvalue = Either(Int, Float)
    rvalue = Either(Int, Float)
    diff = Property(depends_on='lvalue,rvalue')
    enabled = Property(depends_on='lvalue,rvalue')
    percent_diff = Property(depends_on='lvalue,rvalue')

    def _get_percent_diff(self):
        try:
            return self.diff / self.lvalue * 100
        except ZeroDivisionError:
            return 'NaN'

    def _get_diff(self):
        return self.lvalue - self.rvalue

    def _get_enabled(self):
        return abs(self.diff) > DIFF_TOLERANCE


class StrValue(Value):
    lvalue = Str
    rvalue = Str

    def _get_diff(self):
        return self.lvalue != self.rvalue

    def _get_enabled(self):
        return self.diff

    def _get_percent_diff(self):
        return ''


class DiffEditor(BaseTraitsEditor):
    values = List

    recaller = Instance(MassSpecRecaller)
    selected_row = Int

    left_baselines = Dict
    right_baselines = Dict
    _right = None
    basename = Str

    diffs_only = Bool(True)
    adapter = None

    record_id = ''

    def _diffs_only_changed(self, new):
        if new:
            self.values = [vi for vi in self.ovalues if vi.enabled]
            self.adapter.use_bg_color = False
        else:
            self.adapter.use_bg_color = True
            self.values = self.ovalues

    def setup(self, left):
        self.record_id = left.record_id
        right = self._find_right(left)
        self.adapter = ValueTabularAdapter()
        if right:
            self._right = right
            return True

    def set_diff(self, left):
        self.name = '{} Diff'.format(left.record_id)
        self.basename = left.record_id

        right = self._right

        isotopes = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
        self._set_values(left, right, isotopes)

    def _find_right(self, left):
        """
            find corresponding analysis in secondary database
        """
        recaller = self.recaller

        # if recaller.connect():
        return recaller.find_analysis(left.labnumber, left.aliquot,
                                      left.step)

    def _set_values(self, left, right, isotopes):
        vs = []
        pfunc = lambda x: lambda n: u'{} {}'.format(x, n)

        vs.append(Value(name='J',
                        lvalue=nominal_value(left.j),
                        rvalue=nominal_value(right.j)))
        vs.append(Value(name=u'J {}'.format(PLUSMINUS_ONE_SIGMA),
                        lvalue=std_dev(left.j),
                        rvalue=std_dev(right.j)))
        vs.append(Value(name='Age',
                        lvalue=left.age,
                        rvalue=right.age))
        vs.append(Value(name=u'Age {}'.format(PLUSMINUS_ONE_SIGMA),
                        lvalue=left.age_err,
                        rvalue=right.age_err))
        # vs.append(Value(name=u'\u00b1 w/o JEr',
        #                 lvalue=std_dev(left.uage_w_j_err),
        #                 rvalue=right.age_err_w_j))
        vs.append(Value(name='40Ar* %',
                        lvalue=nominal_value(left.rad40_percent),
                        rvalue=nominal_value(right.rad40_percent)))

        for a in isotopes:
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            func = pfunc(a)

            i = iso.uvalue
            vs.append(Value(name=a,
                            lvalue=nominal_value(i),
                            rvalue=riso.value))
            vs.append(Value(name=func(PLUSMINUS_ONE_SIGMA), lvalue=std_dev(i), rvalue=riso.error))

            vs.append(Value(name=func('N'), lvalue=iso.n, rvalue=riso.n))
            vs.append(StrValue(name=func('Fit'), lvalue=iso.fit.lower(), rvalue=riso.fit.lower()))
            vs.append(Value(name=func('Filter'), lvalue=iso.filter_outliers_dict.get('filter_outliers'),
                            rvalue=riso.filter_outliers_dict.get('filter_outliers')))
            vs.append(Value(name=func('IC'), lvalue=nominal_value(iso.ic_factor),
                            rvalue=nominal_value(iso.ic_factor)))

        for a in isotopes:
            func = pfunc(a)
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            vs.append(Value(name=func('Bs'), lvalue=iso.baseline.value, rvalue=riso.baseline.value))
            vs.append(Value(name=func(PLUSMINUS_ONE_SIGMA), lvalue=iso.baseline.error, rvalue=riso.baseline.error))
            vs.append(Value(name=func('Nbs'), lvalue=iso.baseline.n, rvalue=riso.baseline.n))
            self.right_baselines[a] = iso.baseline

        for a in isotopes:
            func = pfunc(a)
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            vs.append(Value(name=func('Blank'), lvalue=iso.blank.value, rvalue=riso.blank.value))
            vs.append(Value(name=func(PLUSMINUS_ONE_SIGMA), lvalue=iso.blank.error, rvalue=riso.blank.error))

        rpr = right.production_ratios
        for k, v in left.production_ratios.iteritems():
            vs.append(Value(name=k, lvalue=nominal_value(v),
                            rvalue=nominal_value(rpr[k])))

        rifc = right.interference_corrections
        for k, v in left.interference_corrections.iteritems():
            vs.append(Value(name=k, lvalue=nominal_value(v),
                            rvalue=nominal_value(rifc[k.lower()])))

        # self.values = vs
        self.ovalues = vs[:]
        self._diffs_only_changed(self.diffs_only)

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('diffs_only'), spring, UItem('record_id', style='readonly'), spring),
            UItem('values', editor=myTabularEditor(adapter=self.adapter,
                                                   editable=False,
                                                   selected_row='selected_row'))))
        return v

# ============= EOF =============================================
