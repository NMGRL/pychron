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
from traits.api import Str, Int
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.condition.condition import BaseCondition


class ExperimentQueueAction(BaseCondition):
    analysis_type = Str
    action = Str

    nrepeat = Int(1)
    count = Int(0)
    def __init__(self, aparams, *args, **kw):
        super(ExperimentQueueAction, self).__init__(*args, **kw)
        self._parse(aparams)

    def _parse(self, params):
        params = eval(params)
        n = len(params)
        nr = 1
        if n == 5:
            at, a, c, ac, nr = params
        elif n == 4:
            at, a, c, ac = params

        self.analysis_type = at
        self.attr = a
        self.comp = c
        self.action = ac
        self.nrepeat = int(nr)

    def to_string(self):
        return '{}{}{}'.format(self.attr, self.comp)

    def _should_check(self, run, data, cnt):
        if run.spec.analysis_type==self.analysis_type:
            return hasattr(run, self.attr)

    def _check(self, run, data):
        run_value = getattr(run, self.attr)
        comp = self.comparator
        cmd = '{}{}'.format(run_value, comp)
        return eval(cmd)

#============= EOF =============================================
