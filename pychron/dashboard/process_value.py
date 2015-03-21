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
import time

from traits.api import HasTraits, Str, Either, Property, Float, Int, Bool, List, Enum
from traitsui.api import View, VGroup, HGroup, UItem, ListEditor, InstanceEditor, Readonly

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.dashboard.conditional import DashboardConditional
from pychron.dashboard.constants import NOERROR, CRITICAL, WARNING


class ProcessValue(HasTraits):
    name = Str
    units = Str
    tag = Str
    func_name = Str
    change_threshold = Float(1e-10)
    period = Either(Float, Str)  # "on_change" or number of seconds
    last_time = Float
    last_time_str = Property(depends_on='last_time')
    enabled = Bool
    last_value = Float
    timeout = Float
    plotid = Int
    conditionals = List(DashboardConditional)
    flag = Enum(NOERROR, WARNING, CRITICAL)

    def is_different(self, v):
        ret = None
        ct = time.time()
        tt = 60 * 60  # max time (s) allowed without a measurement taken
        # even if the current value is the same as the last value

        threshold = self.change_threshold
        if abs(self.last_value - v) > threshold or (self.last_time and ct - self.last_time > tt):
            # a = abs(self.last_value - v) > threshold
            # b = (self.last_time and ct - self.last_time > tt)
            # self.debug('a={} {}-{}>{}, b={}'.format(a, self.last_value, v,threshold, b))

            self.last_value = v
            ret = True

        self.last_time = time.time()
        return ret

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('enabled'), Readonly('name')),
                        VGroup(HGroup(Readonly('tag'),
                                      Readonly('period')),
                               HGroup(Readonly('last_time_str'),
                                      Readonly('last_value')),
                               VGroup(UItem('conditionals', editor=ListEditor(editor=InstanceEditor(),
                                                                              style='custom',
                                                                              mutable=False)),
                                      show_border=True,
                                      label='Conditionals'),
                               enabled_when='enabled')))
        return v

    def _get_last_time_str(self):
        r = ''
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r

# ============= EOF =============================================



