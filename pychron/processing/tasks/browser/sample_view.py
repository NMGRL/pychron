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
from traits.api import Instance
from traitsui.api import View, Item, UItem, VSplit, VGroup, EnumEditor, HGroup, TabularEditor, CheckListEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.tasks.browser.pane_model_view import PaneModelView
from pychron.processing.tasks.browser.tables import Tables, TableTools


class BrowserSampleView(PaneModelView):
    tableview = Instance(Tables)
    tabletools = Instance(TableTools)
    def _tableview_default(self):
        return Tables(model=self.model, pane=self.pane)

    def _tabletools_default(self):
        return TableTools(model=self.model, pane=self.pane)

    def traits_view(self):
        irrad_grp = VGroup(UItem('irradiation', editor=EnumEditor(name='irradiations')),
                           UItem('level', editor=EnumEditor(name='levels')),
                           # VGroup(
                           # Item('include_monitors', label='Monitors'),
                           # Item('include_unknowns', label='Unknowns')),
                           icon_button_editor('find_by_irradiation',
                                              'find',
                                              tooltip='Filter Samples by Irradiation/Level', ),
                           enabled_when='not selected_projects',
                           show_border=True,
                           label='Irradiations')

        project_grp = VGroup(HGroup(Item('project_filter', label='Filter'),
                                    icon_button_editor('clear_selection_button',
                                                       'cross',
                                                       tooltip='Clear selected')),
                             UItem('projects',
                                   editor=TabularEditor(editable=False,
                                                        refresh='refresh_needed',
                                                        selected='selected_projects',
                                                        adapter=ProjectAdapter(),
                                                        multi_select=True)),
                             show_border=True,
                             label='Projects')
        analysis_type_group = HGroup(
            Item('use_analysis_type_filtering', label='Enabled'),
            UItem('_analysis_include_types',
                  enabled_when='use_analysis_type_filtering',
                  style='custom',
                  editor=CheckListEditor(cols=5,
                                         name='available_analysis_types')),
            show_border=True,
            label='Analysis Types')

        date_grp = HGroup(UItem('use_low_post'),
                          UItem('low_post', enabled_when='use_low_post'),
                          UItem('use_high_post'),
                          UItem('high_post', enabled_when='use_high_post'),
                          UItem('use_named_date_range'),
                          UItem('named_date_range'),
                          icon_button_editor('date_configure_button', 'view-calendar-month-2.png'),
                          label='Date',
                          show_border=True)
        top_level_filter_grp = VGroup(HGroup(project_grp, irrad_grp),
                                      analysis_type_group,
                                      date_grp)

        grp = VSplit(top_level_filter_grp,
                     UItem('controller.tabletools',
                           style='custom', height=0.1),
                     UItem('controller.tableview',
                           height=0.6,
                           style='custom'))
        return View(grp)
#============= EOF =============================================



