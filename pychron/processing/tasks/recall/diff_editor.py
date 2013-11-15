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
from traits.api import Property, Instance, List, Either, Int, Float, HasTraits, \
    Str, Dict
from traitsui.api import View, UItem, HSplit, TabularEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.helpers.formatting import floatfmt
from pychron.processing.tasks.recall.mass_spec_recaller import MassSpecRecaller


class ValueTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Value', 'value')]
    value_text = Property
    name_width = Int(60)

    def _get_value_text(self):
        return floatfmt(self.item.value)


class DiffTabularAdapter(TabularAdapter):
    columns = [('Diff', 'diff')]
    diff_text = Property

    def _get_diff_text(self):
        return floatfmt(self.item.diff, n=7)


class Value(HasTraits):
    name = Str
    value = Either(Float, Int)


class DiffValue(HasTraits):
    left = Instance(Value)
    right = Instance(Value)
    diff = Property(depends_on='[left,right].value')

    def _get_diff(self):
        return self.left.value - self.right.value


class DiffEditor(BaseTraitsEditor):
    #model = Any
    #analysis_view = Instance('pychron.processing.analyses.analysis_view.AnalysisView')
    #analysis_summary = Any

    #name = Property(depends_on='analysis_view.analysis_id')
    left_values = List
    diff_values = List
    right_values = List

    recaller = Instance(MassSpecRecaller, ())
    selected_row = Int

    left_baselines = Dict
    right_baselines = Dict

    def set_diff(self, left):
        right = self._find_right(left)

        isotopes = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
        self._set_left(left, isotopes)
        self._set_right(right, isotopes)

        rr = []
        for l, r in zip(self.left_values, self.right_values):
            d = DiffValue(left=l, right=r)
            rr.append(d)
        self.diff_values = rr


        #print self.left_baselines['Ar40'].ys ==self.right_baselines['Ar40'].ys
        #print self.right_baselines['Ar40'].ys

    def _find_right(self, left):
        """
            find corresponding analysis in secondary database
        """
        recaller = self.recaller

        if recaller.connect():
            return recaller.find_analysis(left.labnumber, left.aliquot,
                                          left.step)

    def _set_left(self, item, isotopes):
        vs = []
        err = u'\u00b11\u03c3'
        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name=a, value=iso.value))
            vs.append(Value(name=err, value=iso.error))

        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name='{}Bs'.format(a), value=iso.baseline.value))
            vs.append(Value(name=err, value=iso.baseline.error))
            vs.append(Value(name='Nbs', value=len(iso.baseline.xs)))
            self.left_baselines[a] = iso.baseline

        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name='{}Bl'.format(a), value=iso.blank.value))
            vs.append(Value(name=err, value=iso.blank.error))

        self.left_values = vs

    def _set_right(self, item, isotopes):
        vs = []
        err = u'\u00b11\u03c3'
        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name=a, value=iso.value))
            vs.append(Value(name=err, value=iso.error))

        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name='{}Bs'.format(a), value=iso.baseline.value))
            vs.append(Value(name=err, value=iso.baseline.error))
            vs.append(Value(name='Nbs', value=len(iso.baseline.xs)))
            self.right_baselines[a] = iso.baseline

        for a in isotopes:
            iso = item.isotopes[a]
            vs.append(Value(name='{}Bl'.format(a), value=iso.blank.value))
            vs.append(Value(name=err, value=iso.blank.error))

        self.right_values = vs

    def traits_view(self):
        l = UItem('left_values',
                  editor=TabularEditor(adapter=ValueTabularAdapter(),
                                       editable=False,
                                       selected_row='selected_row'))
        d = UItem('diff_values',
                  editor=TabularEditor(adapter=DiffTabularAdapter(),
                                       editable=False,
                                       selected_row='selected_row'))
        r = UItem('right_values',
                  editor=TabularEditor(adapter=ValueTabularAdapter(),
                                       editable=False,
                                       selected_row='selected_row'))
        v = View(HSplit(l, d, r))
        return v

        #def _get_name(self):
        #    #if self.model and self.model.analysis_view:
        #    if self.analysis_view:
        #        return self.analysis_view.analysis_id
        #    else:
        #        return 'None'

#============= EOF =============================================
