# ===============================================================================
# Copyright 2020 ross
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
from numpy import array
from uncertainties import nominal_value, std_dev

from pychron.pipeline.nodes.data import DVCNode


class DSCorrelationNode(DVCNode):
    name = "DS Correlation"
    configurable = False

    def run(self, state):
        # print('asdf', state.unknowns)
        xs = array([nominal_value(a.uage) for a in state.unknowns])
        exs = array([std_dev(a.uage) for a in state.unknowns])
        ys = array([nominal_value(a.kca) for a in state.unknowns])
        eys = array([std_dev(a.kca) for a in state.unknowns])

        xmin = min(xs - exs)
        xmax = max(xs + exs)
        ymin = min(ys - eys)
        ymax = max(ys + eys)

        # find relevant saved ellipses
        es = self.dvc.meta_repo.get_correlation_ellipses()
        cs = []
        for k, v in es.items():
            a, kca = v["age"], v["kca"]
            amin, amax = a["min"], a["max"]
            kmin, kmax = kca["min"], kca["max"]
            if (
                xmin < amin < xmax
                and xmin < amax < xmax
                and ymin < kmin < ymax
                and ymin < kmax < ymax
            ):
                cs.append((k, v))

        state.correlation_ellipses = cs


# ============= EOF =============================================
