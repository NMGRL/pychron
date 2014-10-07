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
from traits.api import HasTraits, List, Int
from traitsui.api import View, UItem, TabularEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class ConditionsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Check', 'comp'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Value', 'value')]

    attr_width=Int(100)
    check_width=Int(200)
    start_width=Int(50)
    frequency_width=Int(100)
    value_width=Int(120)

class ConditionsView(HasTraits):
    termination_conditions = List

    def traits_view(self):
        editor = TabularEditor(adapter=ConditionsAdapter(),
                               editable=False,
                               auto_update=True)

        v = View(UItem('termination_conditions',
                       editor=editor),
                 title='Current Conditions',
                 width=800,
                 resizable=True)
        return v

#============= EOF =============================================



