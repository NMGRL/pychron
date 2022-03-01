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
from traitsui.api import View, UItem, TabularEditor
from uncertainties import nominal_value

from pychron.core.pychron_traits import BorderVGroup
from pychron.pipeline.plot.editors.base_matrix_table import BaseMatrixTable
from pychron.pipeline.results.base_matrix_result import BaseMatrixResult


class Results(BaseMatrixResult):
    def _calculate_values(self, ag, others):
        vs = [""]
        aa = [nominal_value(a.uage) for a in ag.clean_analyses()]
        for other in others:
            if other == ag:
                pv = ""
            else:
                bb = [nominal_value(a.uage) for a in other.clean_analyses()]
                tstat, pv = ttest_ind(aa, bb, equal_var=False)
            vs.append(pv)

        return vs


class TTestTable(BaseMatrixTable):
    result_klass = Results

    def traits_view(self):
        v = View(
            BorderVGroup(
                UItem("results", editor=TabularEditor(adapter=self.adapter)),
                label="T-test Probabilities",
            )
        )
        return v


if __name__ == "__main__":

    class AGroup:
        def __init__(self, identiifer):
            self.identifier = identiifer

    ags = [AGroup("foo1"), AGroup("bar2")]
    t = TTestTable(ags)
    t.configure_traits()
# ============= EOF =============================================
