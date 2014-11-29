# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, TableEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn


class EmailPane(TraitsTaskPane):
    def traits_view(self):
        cols = [CheckboxColumn(name='enabled'),
                ObjectColumn(name='name', editable=False),
                ObjectColumn(name='email', editable=False),
                ObjectColumn(name='level')]

        v = View(UItem('object.users',
                       editor=TableEditor(columns=cols,
                                          sortable=False)))
        return v

        # ============= EOF =============================================
