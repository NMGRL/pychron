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
    Str, Dict
from traitsui.api import View, UItem, HSplit, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.core.helpers.formatting import floatfmt
from pychron.processing.tasks.recall.mass_spec_recaller import MassSpecRecaller
from pychron.pychron_constants import LIGHT_GREEN, LIGHT_RED_COLOR


class ValueTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Pychron', 'lvalue'),
               ('Diff', 'diff'),
               ('MassSpec', 'rvalue')]

    lvalue_width = Int(100)
    diff_width = Int(100)
    rvalue_width = Int(100)
    name_width = Int(100)

    lvalue_text = Property
    diff_text = Property
    rvalue_text = Property
    name_width = Int(60)
    font = '10'

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        v = self.item.diff
        if abs(v) > 1e-8:
            color = '#FFCCCC'
        return color

    def _get_lvalue_text(self):
        v = self.item.lvalue
        return self._get_value_text(v)

    def _get_rvalue_text(self):
        v = self.item.rvalue
        return self._get_value_text(v)

    def _get_value_text(self, v):
        if isinstance(v, float):
            v = floatfmt(v, n=8)
        return v

    def _get_diff_text(self):
        v = self.item.diff
        if isinstance(v, float):
            if abs(v) < 1e-8:
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

    def _get_diff(self):
        return self.lvalue - self.rvalue


class StrValue(Value):
    lvalue = Str
    rvalue = Str

    def _get_diff(self):
        return self.lvalue != self.rvalue


class DiffEditor(BaseTraitsEditor):
    values = List

    recaller = Instance(MassSpecRecaller, ())
    selected_row = Int

    left_baselines = Dict
    right_baselines = Dict
    _right = None
    basename = Str

    def setup(self, left):
        right = self._find_right(left)
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

        if recaller.connect():
            return recaller.find_analysis(left.labnumber, left.aliquot,
                                          left.step)

    def _set_values(self, left, right, isotopes):
        vs = []
        err = u'\u00b11\u03c3'
        for a in isotopes:
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            vs.append(Value(name=a, lvalue=iso.value, rvalue=riso.value))
            vs.append(Value(name=err, lvalue=iso.error, rvalue=riso.error))
            vs.append(Value(name='N', lvalue=iso.n, rvalue=riso.n))
            vs.append(StrValue(name='Fit', lvalue=iso.fit, rvalue=riso.fit))

        for a in isotopes:
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            vs.append(Value(name='{}Bs'.format(a), lvalue=iso.baseline.value, rvalue=riso.baseline.value))
            vs.append(Value(name=err, lvalue=iso.baseline.error, rvalue=riso.baseline.error))
            vs.append(Value(name='Nbs', lvalue=iso.baseline.n, rvalue=riso.baseline.n))
            self.right_baselines[a] = iso.baseline

        for a in isotopes:
            iso = left.isotopes[a]
            riso = right.isotopes[a]
            vs.append(Value(name='{}Bl'.format(a), lvalue=iso.blank.value, rvalue=riso.blank.value))
            vs.append(Value(name=err, lvalue=iso.blank.error, rvalue=riso.blank.error))

        self.values = vs

    def traits_view(self):
        v = View(UItem('values', editor=TabularEditor(adapter=ValueTabularAdapter(),
                                                      editable=False,
                                                      selected_row='selected_row')))
        return v

#============= EOF =============================================
