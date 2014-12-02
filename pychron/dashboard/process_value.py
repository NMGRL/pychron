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
from traits.api import HasTraits, Button, Str, Either, Property, Float, Int, Bool, List
from traitsui.api import View, Item, VGroup, HGroup, UItem, ListEditor, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.dashboard.conditional import DashboardConditional


class ProcessValue(HasTraits):
    name = Str
    tag = Str
    func_name = Str

    period = Either(Float, Str)  # "on_change" or number of seconds
    last_time = Float
    last_time_str = Property(depends_on='last_time')
    enabled = Bool
    last_value = Float
    timeout = Float
    plotid = Int
    conditionals = List(DashboardConditional)

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('enabled'), Item('name')),
                        VGroup(HGroup(Item('tag'),
                                      Item('period')),
                               HGroup(Item('last_time_str', style='readonly'),
                                      Item('last_value', style='readonly')),
                               UItem('conditionals', editor=ListEditor(editor=InstanceEditor(),
                                                                       style='custom',
                                                                       mutable=False)),
                               enabled_when='enabled')))
        return v

    def _get_last_time_str(self):
        r = ''
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r
# ============= EOF =============================================



