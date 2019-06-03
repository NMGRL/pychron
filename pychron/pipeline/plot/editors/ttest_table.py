# ===============================================================================
# Copyright 2019 ross
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
from scipy.stats import ttest_ind
from traits.api import HasTraits, List, Instance
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value

from pychron.core.helpers.formatting import floatfmt
from pychron.core.pychron_traits import BorderVGroup


class Result(HasTraits):
    def __init__(self, ag, ags):
        self.values = self._calculate_values(ag, ags)
        self.name = ag.identifier

    def _calculate_values(self, ag, others):
        vs = ['']
        aa = [nominal_value(a.uage) for a in ag.clean_analyses()]
        for other in others:
            if other == ag:
                pv = ''
            else:
                bb = [nominal_value(a.uage) for a in other.clean_analyses()]
                tstat, pv = ttest_ind(aa, bb, equal_var=False)
            vs.append(pv)

        return vs

    def get_value(self, row, column):
        if column == 0:
            return self.name
        elif column < row:
            return ''
        else:
            ret = self.values[column + 1]
            if ret:
                ret = floatfmt(ret, 3)

        return ret

    def get_color(self, row, column):
        if column == 0:
            return 'white'
        elif column < row:
            return 'white'
        else:
            v = self.values[column + 1]
            return 'white' if not v or v < 0.05 else 'lightgreen'


class ResultsAdapter(TabularAdapter):
    def get_text(self, obj, trait, row, column):
        return getattr(obj, trait)[row].get_value(row, column)

    def get_bg_color(self, obj, trait, row, column=0):
        return getattr(obj, trait)[row].get_color(row, column)


class TTestTable(HasTraits):
    results = List
    adapter = Instance(TabularAdapter)

    def __init__(self, ags, *args, **kw):
        super().__init__(*args, **kw)

        self.analysis_groups = ags

        self.adapter = self._make_adapter(ags)
        self.recalculate()

    def recalculate(self):
        results = [Result(ag, self.analysis_groups) for ag in self.analysis_groups[:-1]]
        self.results = results

    def _make_adapter(self, ags):
        adp = ResultsAdapter()

        cols = [(a.identifier, '{}_value'.format(a.identifier)) for a in ags[1:]]
        adp.columns = [('Identifier', 'name'), ] + cols
        return adp

    def traits_view(self):
        v = View(BorderVGroup(UItem('results', editor=TabularEditor(adapter=self.adapter)),
                              label='T-test Probabilities'))
        return v


if __name__ == '__main__':
    class AGroup:
        def __init__(self, identiifer):
            self.identifier = identiifer


    ags = [AGroup('foo1'), AGroup('bar2')]
    t = TTestTable(ags)
    t.configure_traits()
# ============= EOF =============================================
