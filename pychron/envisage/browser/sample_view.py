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

class BaseBrowserSampleView(PaneModelView):
    def _get_irrad_group(self):
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
        return irrad_grp

    def _get_project_group(self):
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
        return project_grp

    def _get_experiments_group(self):
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
        return exp_grp

    def _get_analysis_type_group(self):
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
        return analysis_type_group

    def _get_date_group(self):
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
        return date_grp

    def _get_mass_spectrometer_group(self):
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
        return ms_grp

    def _get_identifier_group(self):
        ln_grp = HGroup(
            UItem('identifier'),
            label='Identifier', show_border=True,
            visible_when='identifier_visible')
        return ln_grp

    def _get_sample_group(self):
        irrad_grp = self._get_irrad_group()
        project_grp = self._get_project_group()
        exp_grp = self._get_experiments_group()
        analysis_type_group = self._get_analysis_type_group()
        date_grp = self._get_date_group()
        ms_grp = self._get_mass_spectrometer_group()
        ln_grp = self._get_identifier_group()

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
        return grp


class BrowserSampleView(BaseBrowserSampleView):
    # tableview = Instance(TableView)

    # def _tableview_default(self):
    #     return TableView(model=self.model, pane=self.pane)
    def trait_context(self):
        ctx = super(BrowserSampleView, self).trait_context()
        ctx['analysis_table'] = self.model.analysis_table
        return ctx

    def traits_view(self):
        # def make_name(name):
        #     return 'object.analysis_table.{}'.format(name)

        analysis_tools = HGroup(UItem('analysis_table.analysis_filter_parameter',
                                      width=-90,
                                      editor=EnumEditor(name='analysis_table.analysis_filter_parameters')),
                                UItem('analysis_table.analysis_filter'))
        # UItem(make_name('analysis_filter'),
        #       editor=ComboboxEditor(name=make_name('analysis_filter_values'))))

        agrp = VGroup(analysis_tools,
                      UItem('analysis_table.analyses',
                            width=0.4,
                            editor=myTabularEditor(
                                adapter=self.model.analysis_table.tabular_adapter,
                                operations=['move', 'delete'],
                                column_clicked='analysis_table.column_clicked',
                                refresh='analysis_table.refresh_needed',
                                selected='analysis_table.selected',
                                dclicked='analysis_table.dclicked',
                                multi_select=self.pane.multi_select,
                                drag_external=True,
                                scroll_to_row='analysis_table.scroll_to_row',
                                stretch_last_section=False)),
                      # HGroup(spring, Item(make_name('omit_invalid'))),
                      defined_when=self.pane.analyses_defined,
                      show_border=True,
                      label='Analyses')

        sample_grp = self._get_sample_group()
        return View(HGroup(sample_grp, agrp))

    def unselect_projects(self, info, obj):
        obj.selected_projects = []

    def unselect_analyses(self, info, obj):
        obj.selected = []

    def configure_analysis_table(self, info, obj):
        # self.model.analysis_table.configure_table()
        obj.configure_table()

    def recall_items(self, info, obj):
        obj.context_menu_event = ('open', {'open_copy': False})

    def review_status_details(self, info, obj):
        obj.review_status_details()


class BrowserInterpretedAgeView(BaseBrowserSampleView):
    def trait_context(self):
        ctx = super(BrowserInterpretedAgeView, self).trait_context()
        ctx['interpreted_table'] = self.model.interpreted_age_table
        return ctx

    def _get_interpreted_age_group(self):
        grp = VGroup(
            UItem('interpreted_table.interpreted_ages',
                  width=0.4,
                  editor=myTabularEditor(
                      adapter=self.model.interpreted_age_table.tabular_adapter,
                      operations=['move', 'delete'],
                      # column_clicked=make_name('column_clicked'),
                      # refresh='interpreted_table.refresh_needed',
                      selected='interpreted_table.selected',
                      # dclicked='interpreted_table.dclicked',
                      multi_select=True,
                      # drag_external=True,
                      # scroll_to_row='interpreted_table.scroll_to_row',
                      stretch_last_section=False)),
            # HGroup(spring, Item(make_name('omit_invalid'))),
            show_border=True,
            label='Interpreted Ages')

        return grp

    def traits_view(self):
        sample_grp = self._get_sample_group()
        ia_grp = self._get_interpreted_age_group()
        v = View(HGroup(sample_grp, ia_grp))
        return v

# ============= EOF =============================================
