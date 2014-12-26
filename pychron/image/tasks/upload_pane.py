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
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import HasTraits, Button, Str
from traitsui.api import View, Item, UItem, TabularEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class ImageAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Sample', 'sample')]


class UploadPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('items', editor=TabularEditor(adapter=ImageAdapter(),
                                                     editable=False,
                                                     selected='selected_items',
                                                     auto_update=True,
                                                     multi_select=True)))
        return v

# ============= EOF =============================================



