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
from traits.api import HasTraits, List, Instance, Int
from traitsui.tabular_adapter import TabularAdapter

from pychron.pipeline.results.base_matrix_result import BaseMatrixResult


class ResultsAdapter(TabularAdapter):
    name_width = Int(50)

    def get_text(self, obj, trait, row, column):
        return getattr(obj, trait)[row].get_value(row, column)

    def get_bg_color(self, obj, trait, row, column=0):
        return getattr(obj, trait)[row].get_color(row, column)


class BaseMatrixTable(HasTraits):
    results = List
    adapter = Instance(TabularAdapter)
    result_klass = Instance(BaseMatrixResult)

    def __init__(self, ags, *args, **kw):
        super().__init__(*args, **kw)

        self.analysis_groups = ags

        self.adapter = self._make_adapter(ags)
        self.recalculate()

    def recalculate(self):
        results = [self.result_klass(ag, self.analysis_groups) for ag in self.analysis_groups[:-1]]
        self.results = results

    def _make_adapter(self, ags):
        adp = ResultsAdapter()
        cols = [(a.identifier, '{}_value'.format(a.identifier)) for a in ags[1:]]
        adp.columns = [('Identifier', 'name'), ] + cols
        return adp
# ============= EOF =============================================
