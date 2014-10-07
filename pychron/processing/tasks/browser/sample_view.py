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
from traitsui.api import View, UItem, VSplit, VGroup, EnumEditor,\
    HGroup, TabularEditor, CheckListEditor, spring
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.tasks.browser.pane_model_view import PaneModelView
from pychron.processing.tasks.browser.tableview import TableView, TableTools


class BrowserSampleView(PaneModelView):
    tableview = Instance(TableView)
    tabletools = Instance(TableTools)

    def _tableview_default(self):
        return TableView(model=self.model, pane=self.pane)

    def _tabletools_default(self):
        return TableTools(model=self.model, pane=self.pane)

    def traits_view(self):
        # irrad_grp = VGroup(
        #     UItem('irradiation_enabled', tooltip='Enable Irradiation filter'),
        #     VGroup(UItem('irradiation', editor=EnumEditor(name='irradiations')),
        #            UItem('level', editor=EnumEditor(name='levels')),
        #            enabled_when='irradiation_enabled'),
        #     show_border=True,
        #     label='Irradiations')

        irrad_grp = VGroup(
            HGroup(UItem('irradiation_enabled',
                         tooltip='Enable Irradiation filter'),
                   UItem('irradiation',
                         enabled_when='irradiation_enabled',
                         editor=EnumEditor(name='irradiations'))),
            UItem('level',
                  enabled_when='irradiation_enabled',
                  editor=EnumEditor(name='levels')),
            show_border=True,
            label='Irradiations')

        tgrp = HGroup(UItem('project_enabled', label='Enabled',
                            tooltip='Enable Project filter'),
                      UItem('project_filter',
                            tooltip='Filter list of projects',
                            label='Filter'),
                      icon_button_editor('clear_selection_button',
                                         'cross',
                                         tooltip='Clear selected'))
        pgrp = UItem('projects',
                     editor=TabularEditor(editable=False,
                                          refresh='refresh_needed',
                                          selected='selected_projects',
                                          adapter=ProjectAdapter(),
                                          multi_select=True),
                     enabled_when='project_enabled')

        project_grp = VGroup(tgrp,pgrp,
                             show_border=True,
                             label='Projects')

        analysis_type_group = HGroup(
            UItem('use_analysis_type_filtering',
                  tooltip='Enable Analysis Type filter',
                  label='Enabled'),
            spring,
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

        ms_grp = HGroup(UItem('use_mass_spectrometers',
                              tooltip='Enable Mass Spectrometer filter'),
                        spring,
                        UItem('mass_spectrometer_includes',
                              style='custom',
                              enabled_when='use_mass_spectrometers',
                              editor=CheckListEditor(name='available_mass_spectrometers',
                                                     cols=10)),
                        label='Mass Spectrometer', show_border=True)

        top_level_filter_grp = VGroup(ms_grp,
                                      HGroup(project_grp, irrad_grp),
                                      analysis_type_group,
                                      date_grp)

        g1 = VGroup(UItem('controller.tabletools',
                          style='custom', height=0.1),
                    UItem('controller.tableview',
                          height=0.6,
                          style='custom'))

        grp = VSplit(top_level_filter_grp, g1)
        return View(grp)

    def unselect_projects(self, info, obj):
        obj.selected_projects = []


# ============= EOF =============================================



