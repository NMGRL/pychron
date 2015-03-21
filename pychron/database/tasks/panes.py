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
from traits.api import HasTraits, Button
from traitsui.api import View, Item, UItem, TabularEditor, VGroup, UReadonly, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================

from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.icon_button_editor import icon_button_editor


class StatusItemsAdapter(TabularAdapter):
    columns = [('Name', 'display_name'),
               ('Value', 'value')]


class SlavePane(TraitsTaskPane):
    def traits_view(self):
        auth_grp = VGroup(Item('host'),
                          Item('user'),
                          Item('password'),
                          show_border=True,
                          label='Authentication')

        v = View(VGroup(auth_grp,
                        HGroup(icon_button_editor('check_status_button', 'database_go_fatcow',
                                                  tooltip='Check slave status. Equivalent to "Show Slave Status"'),
                               icon_button_editor('start_button', 'start',
                                                  tooltip='Start replication. Equivalent to "Start Slave"',
                                                  enabled_when='not running'),
                               icon_button_editor('stop_button', 'stop',
                                                  tooltip='Stop replication. Equivalent to "Stop Slave"',
                                                  enabled_when='running'),
                               icon_button_editor('skip_button', 'skip_occurrence',
                                                  tooltip='Set global skip counter.\n'
                                                          'Equivalent to "Stop Slave;'
                                                          'Set GLOBAL SQL_SKIP_COUNTER=N;Start Slave;"\n'
                                                          'where N is the number of SQL statements to skip'),
                               UItem('skip_count',
                                     tooltip='Number of SQL statements to skip')),
                        UItem('status_items', editor=TabularEditor(adapter=StatusItemsAdapter(),
                                                                   editable=False)),
                        VGroup(UReadonly('last_error',
                                         height=200,
                                         style_sheet='color: red; font-weight: bold'),
                               label='Error',
                               show_border=True),
                        label='Slave',
                        show_border=True))

        v.width = 500
        return v

# ============= EOF =============================================



