# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, VGroup, HGroup, Group, VSplit

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TableEditor, InstanceEditor, ListEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.core.ui.custom_label_editor import CustomLabel


class DashboardCentralPane(TraitsTaskPane):
    def traits_view(self):
        url = CustomLabel('object.notifier.url', label='URL')

        agrp = VGroup(UItem('devices', editor=ListEditor(mutable=False,
                                                         style='custom',
                                                         editor=InstanceEditor(
                                                             view=View(UItem('graph', style='custom'))))), label='All')
        igrp = VGroup(UItem('selected_device', style='custom'), label='Individual')
        tgrp = HGroup(url, UItem('clear_button', tooltip='Clear current errors'))

        # v = View(
        # VGroup(HGroup(url, UItem('clear_button', tooltip='Clear current errors')),
        #            UItem('selected_device',
        #                  style='custom'),
        #
        #     )))
        v = View(VGroup(tgrp, Group(agrp, igrp, layout='tabbed')))
        return v


class DashboardDevicePane(TraitsDockPane):
    id = 'pychron.dashboard.devices'

    def traits_view(self):
        cols = [CheckboxColumn(name='use'),
                ObjectColumn(name='name', editable=False)]

        editor = TableEditor(columns=cols,
                             selected='selected_device')

        cols = [ObjectColumn(name='name', label='Name'),
                ObjectColumn(name='last_value', label='Value'),
                ObjectColumn(name='last_time_str', label='Timestamp')]

        veditor = TableEditor(columns=cols,
                              editable=False)

        v = View(VSplit(UItem('devices', editor=editor),
                        UItem('values', editor=veditor)))
        return v

        # ============= EOF =============================================
