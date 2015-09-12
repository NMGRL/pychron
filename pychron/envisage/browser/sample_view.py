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
from traitsui.api import View, UItem, VGroup, EnumEditor, \
    HGroup, CheckListEditor, spring, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.browser.pane_model_view import PaneModelView


# from pychron.envisage.browser.tableview import TableView


class BrowserSampleView(PaneModelView):
    # tableview = Instance(TableView)

    # def _tableview_default(self):
    #     return TableView(model=self.model, pane=self.pane)

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

        project_grp = Group(UItem('projects',
                                  height=-150,
                                  editor=FilterTabularEditor(editable=False,
                                                             enabled_cb='project_enabled',
                                                             use_fuzzy=True,
                                                             refresh='refresh_needed',
                                                             selected='selected_projects',
                                                             adapter=ProjectAdapter(),
                                                             multi_select=True)),
                            springy=False,
                            visible_when='project_visible',
                            show_border=True,
                            label='Projects')

        exp_grp = Group(UItem('experiments',
                              height=-150,
                              editor=FilterTabularEditor(editable=False,
                                                         use_fuzzy=True,
                                                         enabled_cb='experiment_enabled',
                                                         refresh='refresh_needed',
                                                         selected='selected_experiments',
                                                         adapter=ProjectAdapter(),
                                                         multi_select=True)),
                        springy=False,
                        visible_when='experiment_visible',
                        show_border=True,
                        label='Experiments')
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

        ms_grp = HGroup(UItem('mass_spectrometers_enabled',
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
            # CustomLabel('filter_label',
            #             style='custom',
            #             width=-1.0,
            #             visible_when='not filter_focus'),
            HGroup(ms_grp, ln_grp),
            HGroup(project_grp, exp_grp, irrad_grp),
            analysis_type_group,
            date_grp)

        # g1 = UItem('controller.tableview', style='custom')

        sample_tools = HGroup(UItem('sample_filter_parameter',
                                    width=-90, editor=EnumEditor(name='sample_filter_parameters')),
                              UItem('sample_filter_comparator'),
                              UItem('sample_filter',
                                    editor=ComboboxEditor(name='sample_filter_values')),
                              icon_button_editor('clear_sample_table',
                                                 'clear',
                                                 tooltip='Clear Sample Table'))
        sample_table = VGroup(sample_tools,
                              UItem('samples',
                                    editor=myTabularEditor(
                                        adapter=self.model.labnumber_tabular_adapter,
                                        editable=False,
                                        selected='selected_samples',
                                        multi_select=True,
                                        dclicked='dclicked_sample',
                                        column_clicked='column_clicked',
                                        # update='update_sample_table',
                                        # refresh='update_sample_table',
                                        stretch_last_section=False)),
                              show_border=True, label='Samples')
        grp = VGroup(top_level_filter_grp, sample_table)

        def make_name(name):
            return 'object.analysis_table.{}'.format(name)

        analysis_tools = HGroup(UItem(make_name('analysis_filter_parameter'),
                                      width=-90,
                                      editor=EnumEditor(name=make_name('analysis_filter_parameters'))),
                                UItem(make_name('analysis_filter')))
        # UItem(make_name('analysis_filter'),
        #       editor=ComboboxEditor(name=make_name('analysis_filter_values'))))

        agrp = VGroup(analysis_tools,
                      UItem(make_name('analyses'),
                            width=0.4,
                            editor=myTabularEditor(
                                adapter=self.model.analysis_table.tabular_adapter,
                                operations=['move', 'delete'],
                                column_clicked=make_name('column_clicked'),
                                refresh=make_name('refresh_needed'),
                                selected=make_name('selected'),
                                dclicked=make_name('dclicked'),
                                multi_select=self.pane.multi_select,
                                drag_external=True,
                                scroll_to_row=make_name('scroll_to_row'),
                                stretch_last_section=False)),
                      # HGroup(spring, Item(make_name('omit_invalid'))),
                      defined_when=self.pane.analyses_defined,
                      show_border=True,
                      label='Analyses')

        return View(HGroup(grp, agrp))

    def unselect_projects(self, info, obj):
        obj.selected_projects = []

    def unselect_analyses(self, info, obj):
        obj.selected = []

    def configure_analysis_table(self, info, obj):
        self.model.analysis_table.configure_table()

    def recall_items(self, info, obj):
        obj.context_menu_event = ('open', {'open_copy': False})

# ============= EOF =============================================
