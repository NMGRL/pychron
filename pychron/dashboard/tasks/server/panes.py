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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.editors import TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.core.ui.custom_label_editor import CustomLabel


class DashboardCentralPane(TraitsTaskPane):
    def traits_view(self):
        url = CustomLabel('url', label='URL')
        v = View(
            VGroup(url,
                   UItem('selected_device',
                         style='custom')))

        return v


class DashboardDevicePane(TraitsDockPane):
    id = 'pychron.dashboard.devices'

    def traits_view(self):
        cols = [CheckboxColumn(name='use'),
                ObjectColumn(name='name', editable=False)]

        editor = TableEditor(columns=cols,
                             selected='selected_device')
        v = View(UItem('devices', editor=editor))
        return v

        #============= EOF =============================================
