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
from traits.api import Button
from traitsui.api import View, UItem, VGroup, EnumEditor, \
    HGroup, CheckListEditor, spring, Group, HSplit

from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter, PrincipalInvestigatorAdapter
from pychron.envisage.browser.pane_model_view import PaneModelView
from pychron.envisage.icon_button_editor import icon_button_editor


# from pychron.envisage.browser.tableview import TableView

class BaseBrowserSampleView(PaneModelView):
    configure_date_filter_button = Button
    configure_analysis_type_filter_button = Button
    configure_mass_spectrometer_filter_button = Button

    def _configure_date_filter_button_fired(self):
        v = View(self._get_date_group(), resizable=True,
                 height=150,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='Configure Date Filter')
        self.edit_traits(view=v)

    def _configure_analysis_type_filter_button_fired(self):
        v = View(self._get_analysis_type_group(), resizable=True,
                 height=150,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='Configure Analysis Type Filter')
        self.edit_traits(view=v)

    def _configure_mass_spectrometer_filter_button_fired(self):
        v = View(self._get_mass_spectrometer_group(), resizable=True,
                 height=150,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='Configure Mass Spectrometer Filter')
        self.edit_traits(view=v)

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
                                                             column_index=-1,
                                                             refresh='refresh_needed',
                                                             selected='selected_projects',
                                                             adapter=ProjectAdapter(),
                                                             multi_select=True)),
                            springy=False,
                            visible_when='project_visible',
                            show_border=True,
                            label='Projects')
        return project_grp

    # def _get_repositories_group(self):
    #     exp_grp = Group(UItem('repositories',
    #                           height=-150,
    #                           editor=FilterTabularEditor(editable=False,
    #                                                      use_fuzzy=True,
    #                                                      enabled_cb='repository_enabled',
    #                                                      refresh='refresh_needed',
    #                                                      selected='selected_repositories',
    #                                                      adapter=ProjectAdapter(),
    #                                                      multi_select=True)),
    #                     springy=False,
    #                     visible_when='repository_visible',
    #                     show_border=True,
    #                     label='Repositories')
    #     return exp_grp
    def _get_simple_analysis_type_group(self):
        grp = HGroup(UItem('use_analysis_type_filtering',
                           tooltip='Enable Analysis Type filter'),
                     icon_button_editor('controller.configure_analysis_type_filter_button',
                                        'cog',
                                        tooltip='Configure analysis type filtering',
                                        enabled_when='use_analysis_type_filtering'),
                     show_border=True, label='Analysis Types')
        return grp

    def _get_simple_date_group(self):
        grp = HGroup(icon_button_editor('controller.configure_date_filter_button', 'cog',
                                        tooltip='Configure date filtering'), show_border=True,
                     label='Date')
        return grp

    def _get_simple_mass_spectrometer_group(self):
        grp = HGroup(UItem('mass_spectrometers_enabled',
                           tooltip='Enable Mass Spectrometer filter'),
                     icon_button_editor('controller.configure_mass_spectrometer_filter_button', 'cog',
                                        tooltip='Configure mass_spectrometer filtering'), show_border=True,
                     label='Mass Spectrometer')
        return grp

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

    def _get_pi_group(self):
        pi_grp = Group(UItem('principal_investigators',
                             height=-150,
                             editor=FilterTabularEditor(editable=False,
                                                        use_fuzzy=True,
                                                        enabled_cb='principal_investigator_enabled',
                                                        refresh='refresh_needed',
                                                        selected='selected_principal_investigators',
                                                        adapter=PrincipalInvestigatorAdapter(),
                                                        multi_select=True)),
                       springy=False,
                       visible_when='principal_investigator_visible',
                       show_border=True,
                       label='PI')
        return pi_grp

    def _get_load_group(self):
        load_grp = Group(UItem('selected_load'))
        return load_grp

    def _get_sample_group(self):
        irrad_grp = self._get_irrad_group()
        project_grp = self._get_project_group()

        # analysis_type_group = self._get_analysis_type_group()
        # date_grp = self._get_date_group()
        # ms_grp = self._get_mass_spectrometer_group()

        simple_analysis_type_grp = self._get_simple_analysis_type_group()
        simple_date_grp = self._get_simple_date_group()
        simple_mass_spectrometer_grp = self._get_simple_mass_spectrometer_group()

        # ln_grp = self._get_identifier_group()
        pi_grp = self._get_pi_group()
        load_grp = self._get_load_group()

        top_level_filter_grp = VGroup(
            # CustomLabel('filter_label',
            #             style='custom',
            #             width=-1.0,
            #             visible_when='not filter_focus'),
            HGroup(UItem('fuzzy_search_entry', tooltip='Enter a simple search, Pychron will do the rest.'),
                   label='Search',
                   show_border=True),
            # HGroup(simple_mass_spectrometer_grp, simple_analysis_type_grp, simple_date_grp, ln_grp),
            HGroup(simple_mass_spectrometer_grp, simple_analysis_type_grp, simple_date_grp),
            HGroup(pi_grp, project_grp, irrad_grp, load_grp))
        # analysis_type_group,
        # date_grp)

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
    def trait_context(self):
        ctx = super(BrowserSampleView, self).trait_context()
        ctx['analysis_table'] = self.model.analysis_table
        return ctx

    def traits_view(self):
        analysis_tools = VGroup(HGroup(UItem('analysis_table.analysis_set',
                                             width=-90,
                                             editor=EnumEditor(name='analysis_table.analysis_set_names')),
                                       icon_button_editor('analysis_table.add_analysis_set_button', 'add',
                                                          enabled_when='analysis_table.items',
                                                          tooltip='Add current analyses to an analysis set'),
                                       icon_button_editor('add_analysis_group_button', 'database_add',
                                                          enabled_when='analysis_table.items',
                                                          tooltip='Add current analyses to an analysis group')),
                                HGroup(UItem('analysis_table.analysis_filter_parameter',
                                             width=-90,
                                             editor=EnumEditor(name='analysis_table.analysis_filter_parameters')),
                                       UItem('analysis_table.analysis_filter')))
        agrp = Group(VGroup(analysis_tools,
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
                            defined_when=self.pane.analyses_defined,
                            show_border=True,
                            label='Analyses'))

        sample_grp = self._get_sample_group()
        return View(HSplit(sample_grp, agrp))

    def unselect_projects(self, info, obj):
        obj.selected_projects = []

    def unselect_analyses(self, info, obj):
        obj.selected = []

    def configure_sample_table(self, info, obj):
        obj.configure_sample_table()

    def configure_analysis_table(self, info, obj):
        obj.configure_table()

    def recall_items(self, info, obj):
        obj.context_menu_event = ('open', {'open_copy': False})

    def review_status_details(self, info, obj):
        obj.review_status_details()

    def toggle_freeze(self, info, obj):
        obj.toggle_freeze()

    def load_review_status(self, info, obj):
        obj.load_review_status()

    def load_chrono_view(self, info, obj):
        obj.load_chrono_view()


class BrowserInterpretedAgeView(BaseBrowserSampleView):

    def delete(self, info, obj):
        print 'asfdasfdasdfasdf', info, obj


    def trait_context(self):
        ctx = super(BrowserInterpretedAgeView, self).trait_context()
        ctx['interpreted_table'] = self.model.interpreted_age_table
        return ctx

    def _get_interpreted_age_group(self):
        grp = VGroup(
            UItem('interpreted_table.interpreted_ages',
                  # width=0.4,
                  editor=myTabularEditor(
                      auto_resize=True,
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
