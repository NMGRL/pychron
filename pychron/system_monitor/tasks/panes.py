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

#============= enthought library imports =======================
from datetime import datetime

from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Instance, Property, Int, Color, Str
from traitsui.api import View, UItem, TabularEditor, VGroup


#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.processing.tasks.analysis_edit.panes import TablePane
from pychron.pychron_constants import LIGHT_RED
from pychron.system_monitor.tasks.connection_spec import ConnectionSpec
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.processing.tasks.analysis_edit.adapters import UnknownsAdapter


class AnalysisAdapter(UnknownsAdapter):
    record_id_width = Int(80)
    sample_width = Int(80)
    age_width = Int(70)
    error_width = Int(60)
    tag_width = Int(50)

    font = 'arial 10'


class AnalysisPane(TablePane):
    name = 'Analyses'
    id = 'pychron.sys_mon.analyses'
    n = Property(depends_on='items')

    def _get_n(self):
        return 'N Runs = {:02n}'.format(len(self.items))

    def traits_view(self):
        v = View(
            CustomLabel('n', color='blue'),
            UItem('items',
                  editor=TabularEditor(
                      editable=False,
                      refresh='refresh_needed',
                      adapter=AnalysisAdapter())))
        return v


class ConnectionPane(TraitsDockPane):
    name = 'Connection'
    id = 'pychron.sys_mon.connection'

    conn_spec = Instance(ConnectionSpec)

    connection_status = Str
    connection_color = Color('red')

    def traits_view(self):
        v = View(VGroup(UItem('conn_spec', style='custom'),
                        UItem('_'),
                        CustomLabel('connection_status',
                                    color_name='connection_color')))
        return v


class DashboardTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               ('Time', 'last_time')]

    last_time_text = Property

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if self.item.timed_out or not self.item.last_time:
            color = LIGHT_RED
        return color

    def _get_last_time_text(self):
        ret = ''
        if self.item.last_time:
            dt = datetime.fromtimestamp(self.item.last_time)
            ret = dt.strftime('%I:%M:%S %p')
        return ret


class DashboardPane(TraitsDockPane):
    id = 'pychron.dashboard.client'
    name = 'Dashboard'

    def traits_view(self):
        #cols=[ObjectColumn(name='name'),
        #      ObjectColumn(name='value'),
        #      ObjectColumn(name='last_time_str', label='Time')]
        #editor=TableEditor(columns=cols, editable=False)
        #v=View(UItem('values',
        #             editor=TableEditor(columns=cols, editable=False)))
        editor = TabularEditor(adapter=DashboardTabularAdapter(),
                               auto_update=True,
                               editable=False)

        v = View(UItem('values',
                       editor=editor))
        return v

        # ============= EOF =============================================
