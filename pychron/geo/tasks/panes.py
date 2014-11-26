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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Instance
from traitsui.api import View, Item, VGroup, HGroup, Label, TabularEditor, UItem, EnumEditor, VSplit
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter, SampleAdapter
from pychron.envisage.icon_button_editor import icon_button_editor


class PointsAdapter(TabularAdapter):
    columns = [('Name', 'sample'), ('N', 'y'), ('E', 'x')]


def active_point(s):
    return 'object.active_point.{}'.format(s)


class GeoPane(TraitsTaskPane):
    def traits_view(self):
        active_point_grp= HGroup(UItem(active_point('sample'),
                                       style='readonly', width=100),
                                 Item(active_point('age')),
                                      Item(active_point('age_error'), label=u'\u00b11\u03c3'),
                                      Item(active_point('interpreted_age'),
                                           editor=EnumEditor(name=active_point('interpreted_ages'))))

        v = View(VGroup(HGroup(icon_button_editor('append_button', 'add'),
                               icon_button_editor('replace_button', 'arrow_refresh', )),
                        UItem('points', editor=myTabularEditor(adapter=PointsAdapter(),
                                                               operations=['move', 'delete'],
                                                               selected='selected_point',
                                                               dclicked='dclicked_point')),
                        active_point_grp))
        return v


class BrowserPane(TraitsDockPane):
    id = 'pychron.geo.browser'
    sample_tabular_adapter = Instance(SampleAdapter, ())

    def traits_view(self):
        project_grp = VGroup(
            HGroup(Label('Filter'),
                   UItem('project_filter',
                         width=75),
                   icon_button_editor('clear_selection_button',
                                      'cross',
                                      tooltip='Clear selected')),
            UItem('projects',
                  editor=TabularEditor(editable=False,
                                       selected='selected_projects',
                                       adapter=ProjectAdapter(),
                                       multi_select=True),
                  width=75))

        sample_grp = VGroup(
            HGroup(
                #Label('Filter'),
                UItem('sample_filter_parameter',
                      editor=EnumEditor(name='sample_filter_parameters')),
                UItem('sample_filter',
                      width=75),
                UItem('sample_filter',
                      editor=EnumEditor(name='sample_filter_values'),
                      width=-25),
                UItem('filter_non_run_samples',
                      tooltip='Omit non-analyzed samples'),
                icon_button_editor('configure_sample_table',
                                   'cog',
                                   tooltip='Configure Sample Table')),
            UItem('samples',
                  editor=TabularEditor(
                      adapter=self.sample_tabular_adapter,
                      editable=False,
                      selected='selected_samples',
                      multi_select=True,
                      dclicked='dclicked_sample',
                      column_clicked='column_clicked',
                      #update='update_sample_table',
                      #refresh='update_sample_table',
                      stretch_last_section=False),
                  width=75))

        grp = VSplit(
            project_grp,
            sample_grp,
            label='Project/Sample')

        database_label = CustomLabel('datasource_url', color='maroon')
        v = View(VGroup(database_label, grp))
        return v

# ============= EOF =============================================

