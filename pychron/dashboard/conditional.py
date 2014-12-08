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
from traits.api import HasTraits, Button, Float, Str, Int, List, String
from traitsui.api import View, Item, HGroup, spring, Readonly
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.dashboard.constants import WARNING


class DashboardConditional(HasTraits):
    key = 'x'
    value = Float
    teststr = Str
    nfail = Int
    _fail_count = 0

    severity = WARNING
    users = List
    usergroups = List
    state = String
    current_value = Str
    emails = Str
    script = Str

    def check(self, v):
        self.current_value = floatfmt(v)
        ret = eval(self.teststr, {self.key: v})
        if ret:
            if self.nfail:
                if self._fail_count >= self.nfail:
                    self.state = self.severity
                    return True
                else:
                    self._fail_count += 1
                    self.state = 'NFails {}/{}'.format(self._fail_count, self.nfail)
            else:
                return ret
        else:
            self._fail_count = 0
            self.state = ''

        return ret

    def traits_view(self):
        v = View(HGroup(Readonly('teststr', width=-200),
                        Readonly('state'),
                        spring))
        return v

# ============= EOF =============================================



