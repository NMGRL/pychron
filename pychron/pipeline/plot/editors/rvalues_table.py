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
from traitsui.api import View, UItem, TabularEditor

from pychron.core.pychron_traits import BorderVGroup
from pychron.pipeline.plot.editors.base_matrix_table import BaseMatrixTable, ResultsAdapter
from pychron.pipeline.results.base_matrix_result import BaseMatrixResult


class Results(BaseMatrixResult):
    def _set_name(self, ag):
        self.name = str(ag.group_id)

    def _format_value(self, v):
        return '{:0.4f}'.format(v)

    def _calculate_values(self, ag, others):
        vs = ['']
        fstd = ag.weighted_mean_f
        for other in others:
            if other == ag:
                pv = ''
            else:
                pv = other.weighted_mean_f / fstd
            vs.append(pv)

        return vs

    def get_color(self, row, column):
        return 'white'


class RValuesTable(BaseMatrixTable):
    result_klass = Results

    def _make_adapter(self, ags):
        adp = ResultsAdapter()
        cols = [(a.group_id, '{}_value'.format(a.group_id)) for a in ags[1:]]
        adp.columns = [('Group', 'name'), ] + cols
        return adp

    def traits_view(self):
        v = View(BorderVGroup(UItem('results', editor=TabularEditor(adapter=self.adapter)),
                              label='R-values'))
        return v
# ============= EOF =============================================
