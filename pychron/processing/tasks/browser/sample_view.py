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
from traitsui.api import View, UItem, VGroup, EnumEditor, \
    HGroup, CheckListEditor, spring, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.tasks.browser.pane_model_view import PaneModelView
from pychron.processing.tasks.browser.tableview import TableView


class BrowserSampleView(PaneModelView):
    tableview = Instance(TableView)

    def _tableview_default(self):
        return TableView(model=self.model, pane=self.pane)

    def traits_view(self):
        irrad_grp = VGroup(
            HGroup(UItem('irradiation_enabled',
                         tooltip='Enable Irradiation filter'),
                   UItem('irradiation',
                         enabled_when='irradiation_enabled',
                         editor=EnumEditor(name='irradiations'))),
            UItem('level',
                  enabled_when='irradiation_enabled',
                  editor=EnumEditor(name='levels')),
            visible_when='irradiation_visible',
            show_border=True,
            label='Irradiations')

        pgrp = UItem('projects',
                     height=-150,
                     editor=FilterTabularEditor(editable=False,
                                                enabled_cb='project_enabled',
                                                refresh='refresh_needed',
                                                selected='selected_projects',
                                                adapter=ProjectAdapter(),
                                                multi_select=True))

        project_grp = Group(pgrp,
                            springy=False,
                            visible_when='project_visible',
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
            visible_when='analysis_types_visible',
            show_border=True,
            label='Analysis Types')

        date_grp = HGroup(UItem('use_low_post'),
                          UItem('low_post', enabled_when='use_low_post'),
                          UItem('use_high_post'),
                          UItem('high_post', enabled_when='use_high_post'),
                          UItem('use_named_date_range'),
                          UItem('named_date_range'),
                          icon_button_editor('date_configure_button', 'calendar'),
                          label='Date',
                          visible_when='date_visible',
                          show_border=True)

        ms_grp = HGroup(UItem('use_mass_spectrometers',
                              tooltip='Enable Mass Spectrometer filter'),
                        spring,
                        UItem('mass_spectrometer_includes',
                              style='custom',
                              enabled_when='use_mass_spectrometers',
                              editor=CheckListEditor(name='available_mass_spectrometers',
                                                     cols=10)),
                        visible_when='mass_spectrometer_visible',
                        label='Mass Spectrometer', show_border=True)
        ln_grp = HGroup(
            UItem('identifier'),
            label='Identifier', show_border=True,
            visible_when='identifier_visible')

        top_level_filter_grp = VGroup(
            CustomLabel('filter_label',
                        style='custom',
                        width=-1.0,
                        visible_when='not filter_focus'),
            HGroup(ms_grp, ln_grp),
            HGroup(project_grp, irrad_grp),
            analysis_type_group,
            date_grp)

        g1 = UItem('controller.tableview', style='custom')
        grp = VGroup(top_level_filter_grp, g1)
        return View(grp)

    def unselect_projects(self, info, obj):
        obj.selected_projects = []


# ============= EOF =============================================



