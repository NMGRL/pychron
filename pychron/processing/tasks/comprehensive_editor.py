# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import List, Int, Float
from traitsui.api import View, VGroup, Readonly, HGroup
# ============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.stats.core import calculate_weighted_mean, calculate_mswd, get_mswd_limits
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


# class ATabularAdapter(TabularAdapter):
#     columns=[()]


class ComprehensiveEditor(BaseTraitsEditor):
    analyses = List
    min_age = Float
    max_age = Float
    n = Int
    mean = Float
    weighted_mean = Float
    mswd = Float
    mswd_low = Float
    mswd_high = Float

    def load(self):
        ans = self.analyses
        ages = [ai.age for ai in ans]
        errors = [ai.age_err_wo_j for ai in ans]

        self.min_age = min(ages)
        self.max_age = max(ages)
        self.n = n = len(self.analyses)
        self.mean = sum(ages) / float(n)

        wm,we= calculate_weighted_mean(ages, errors)
        self.weighted_mean=wm

        mswd = calculate_mswd(ages, errors, wm=wm)
        self.mswd=mswd
        self.mswd_low,self.mswd_high=get_mswd_limits(n)

    def traits_view(self):
        mswd_grp=HGroup(Readonly('mswd',label='MSWD'),
                        HGroup(Readonly('mswd_low',label='Low'),
                        Readonly('mswd_high',label='High'),
                        show_border=True, label='Acceptable Range'))

        stats_grp = VGroup(Readonly('min_age'),
                           Readonly('max_age'),
                           Readonly('n'),
                           Readonly('mean'),
                           Readonly('weighted_mean'),
                           mswd_grp
                           )
        v = View(stats_grp)
        return v

#============= EOF =============================================



