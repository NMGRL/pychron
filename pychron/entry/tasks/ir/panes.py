# ===============================================================================
# Copyright 2016 Jake Ross
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
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, HGroup, VGroup, TabularEditor, EnumEditor
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================


class IRAdapter(TabularAdapter):
    columns = [('IR', 'ir'), ('Lab Contact', 'lab_contact')]


class IRPane(TraitsTaskPane):
    def traits_view(self):
        t = HGroup(UItem('filter_attr', editor=EnumEditor(name='filter_attrs')), UItem('filter_str'))
        v = View(VGroup(t, UItem('items', editor=TabularEditor(adapter=IRAdapter(),
                                                               editable=False))))
        return v

# ============= EOF =============================================
