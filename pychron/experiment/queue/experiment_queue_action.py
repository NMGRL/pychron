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
from traits.api import HasTraits, Str, Float, Int
from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================

class ExperimentQueueAction(HasTraits):
    analysis_type = Str
    criterion = Str
    comparator = Str
    threshold_value = Float
    action = Str

    nrepeat = Int(1)
    count = Int(0)
    def __init__(self, aparams, *args, **kw):
        super(ExperimentQueueAction, self).__init__(*args, **kw)

        self._parse(aparams)

    def _parse(self, params):

#         print params, type(params)
        params = eval(params)
        n = len(params)
        nr = 1
        if n == 6:
            at, a, c, v, ac, nr = params
        elif n == 5:
            at, a, c, v, ac = params

        self.analysis_type = at
        self.attribute = a
        self.comparator = c
        self.threshold_value = float(v)
        self.action = ac
        self.nrepeat = int(nr)

    def check_run(self, run):
        if run.spec.analysis_type == self.analysis_type:
            if hasattr(run, self.attribute):

                run_value = getattr(run, self.attribute)
                comp = self.comparator
                tvalue = self.threshold_value

                cmd = '{}{}{}'.format(run_value, comp, tvalue)
                if eval(cmd):
                    return True


#============= EOF =============================================
