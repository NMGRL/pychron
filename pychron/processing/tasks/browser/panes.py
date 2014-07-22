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
from pyface.action.menu_manager import MenuManager
from traits.api import Int, Str, Instance, HasTraits, Any
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring, \
    VSplit, TabularEditor, EnumEditor, Heading, HSplit, Group
from pyface.tasks.traits_dock_pane import TraitsDockPane
# from pychron.experiment.utilities.identifier import make_runid
# from traitsui.table_column import ObjectColumn
# from traitsui.list_str_adapter import ListStrAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import CheckListEditor
from traitsui.menu import Action
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.qt.tabular_editor import UnselectTabularEditorHandler
from pychron.envisage.browser.adapters import BrowserAdapter, SampleAdapter, ProjectAdapter
from pychron.processing.tasks.analysis_edit.panes import icon_button_editor
from pychron.core.ui.tabular_editor import myTabularEditor


class AnalysisGroupAdapter(BrowserAdapter):
    all_columns = [('Name', 'name'),
                   ('Created', 'create_date'),
                   ('Modified', 'last_modified')]

    columns = [('Name', 'name'),
               ('Create Date', 'create_date'),
               ('Modified', 'last_modified')]


class AnalysisAdapter(BrowserAdapter):
    all_columns = [('Run ID', 'record_id'),
                   ('Tag', 'tag'),
                   ('Iso Fits', 'iso_fit_status'),
                   ('Blank', 'blank_fit_status'),
                   ('IC', 'ic_fit_status'),
                   ('Flux', 'flux_fit_status'),
                   ('Spec.', 'mass_spectrometer'),
                   ('Meas.', 'meas_script_name'),
                   ('Ext.', 'extract_script_name'),
                   ('Device', 'extract_device')]

    columns = [('Run ID', 'record_id'),
               ('Tag', 'tag')]

    record_id_width = Int(100)
    tag_width = Int(65)
    odd_bg_color = 'lightgray'
    font = 'arial 10'

    def get_menu(self, object, trait, row, column):
        return MenuManager(Action(name='Unselect', action='unselect'),
                           Action(name='Replace', action='replace_items'),
                           Action(name='Append', action='append_items'),
                           Action(name='Open', action='recall_items'),
                           Action(name='Open Copy', action='recall_copies'))

    def get_bg_color(self, obj, trait, row, column=0):
        color = 'white'
        if self.item.is_plateau_step:
            color = 'lightgreen'

        return color


class TablesHandler(UnselectTabularEditorHandler):
    def replace_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('replace', None)
            # obj.replace_event = obj.selected

    def append_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('append', None)
            # obj.append_event = obj.selected

    def recall_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('open', {'open_copy': False})

    def recall_copies(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('open', {'open_copy': True})


class Tables(HasTraits):
    model = Any
    pane = Any

    def trait_context(self):
        return {'object': self.model}

    def traits_view(self):
        group_table = UItem('analysis_groups',
                            label='Groups',
                            width=0.6,
                            editor=TabularEditor(
                                adapter=self.pane.analysis_group_tabular_adapter,
                                editable=False,
                                selected='selected_analysis_groups',
                                multi_select=True,
                                dclicked='dclicked_analysis_group',
                                # column_clicked='column_clicked',
                                # update='update_sample_table',
                                # refresh='update_sample_table',
                                stretch_last_section=False))

        sample_table = UItem('samples',
                             label='Samples',
                             width=0.6,
                             editor=TabularEditor(
                                 adapter=self.pane.sample_tabular_adapter,
                                 editable=False,
                                 selected='selected_samples',
                                 multi_select=True,
                                 dclicked='dclicked_sample',
                                 column_clicked='column_clicked',
                                 # update='update_sample_table',
                                 # refresh='update_sample_table',
                                 stretch_last_section=False))

        def make_name(name):
            return 'object.analysis_table.{}'.format(name)

        analysis_table = VGroup(Heading('Analyses'),
                                UItem(make_name('analyses'),
                                      width=0.4,
                                      editor=myTabularEditor(
                                          adapter=self.pane.analysis_tabular_adapter,
                                          operations=['move'],
                                          refresh=make_name('refresh_needed'),
                                          selected=make_name('selected'),
                                          dclicked=make_name('dclicked'),
                                          multi_select=self.pane.multi_select,
                                          drag_external=True,
                                          scroll_to_row=make_name('scroll_to_row'),
                                          stretch_last_section=False)),
                                HGroup(spring, Item(make_name('omit_invalid'))),
                                defined_when=self.pane.analyses_defined)

        v = View(HSplit(Group(sample_table, group_table,
                              layout='tabbed'), analysis_table),
                 handler=TablesHandler())
        return v


class TableTools(HasTraits):
    model = Any
    pane = Any

    def trait_context(self):
        return {'object': self.model}

    def traits_view(self):
        def make_name(name):
            return 'object.analysis_table.{}'.format(name)

        g1 = HGroup(UItem(make_name('analysis_filter_parameter'),
                          width=-90,
                          editor=EnumEditor(name=make_name('analysis_filter_parameters'))),
                    icon_button_editor(make_name('configure_analysis_table'), 'cog',
                                       tooltip='Configure analysis table'))
        g2 = HGroup(UItem(make_name('analysis_filter'),
                          width=-125),
                    UItem(make_name('analysis_filter'),
                          width=-25,
                          editor=EnumEditor(name=make_name('analysis_filter_values'))))
        analysis_tools = VGroup(g1, g2, defined_when=self.pane.analyses_defined)

        g1 = HGroup(UItem('sample_filter_parameter',
                          width=-90, editor=EnumEditor(name='sample_filter_parameters')),
                    icon_button_editor('configure_sample_table',
                                       'cog',
                                       tooltip='Configure Sample Table'),
                    icon_button_editor('clear_sample_table',
                                       'edit-clear',
                                       tooltip='Clear Sample Table')
        )
        g2 = HGroup(UItem('sample_filter',
                          width=-125),
                    UItem('sample_filter',
                          width=-25,
                          editor=EnumEditor(name='sample_filter_values')))
        sample_tools = VGroup(g1, g2)
        # analysis_tools = VGroup(HGroup(UItem(make_name('analysis_filter_parameter'),
        # width=-90,
        # editor=EnumEditor(name=make_name('analysis_filter_parameters'))),
        # UItem(make_name('analysis_filter'),
        # width=-90),
        # UItem(make_name('analysis_filter'),
        # width=-25,
        #                               editor=EnumEditor(name=make_name('analysis_filter_values'))),
        #                         # icon_button_editor(make_name('configure_analysis_table'), 'cog',
        #                         #                    tooltip='Configure analysis table'),
        #                         defined_when=self.pane.analyses_defined)
        # sample_tools = HGroup(UItem('sample_filter_parameter',
        #                             width=-90,
        #                             editor=EnumEditor(name='sample_filter_parameters')),
        #                       UItem('sample_filter', width=-90),
        #                       UItem('sample_filter',
        #                             width=-25,
        #                             editor=EnumEditor(name='sample_filter_values')),)
        #                       # icon_button_editor('configure_sample_table',
        #                       #                    'cog',
        #                       #                    tooltip='Configure Sample Table'))

        # v = View(VGroup(sample_tools, analysis_tools))
        v = View(HGroup(sample_tools, analysis_tools))
        return v


class BrowserPane(TraitsDockPane):
    name = 'Browser'
    id = 'pychron.browser'
    multi_select = True
    analyses_defined = Str('1')

    sample_tabular_adapter = Instance(SampleAdapter, ())
    analysis_tabular_adapter = Instance(AnalysisAdapter, ())
    analysis_group_tabular_adapter = Instance(AnalysisGroupAdapter, ())

    tableview = Instance(Tables)
    tabletools = Instance(TableTools)

    def _get_browser_group(self):
        irrad_grp = VGroup(UItem('irradiation', editor=EnumEditor(name='irradiations')),
                           UItem('level', editor=EnumEditor(name='levels')),
                           # VGroup(
                           # Item('include_monitors', label='Monitors'),
                           # Item('include_unknowns', label='Unknowns')),
                           icon_button_editor('find_by_irradiation',
                                              'edit-find',
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
                     UItem('pane.tabletools', style='custom', height=0.1),
                     UItem('pane.tableview',
                           height=0.6,
                           style='custom'))
        return grp

    def traits_view(self):
        main_grp = self._get_browser_group()

        v = View(
            VGroup(
                HGroup(icon_button_editor('advanced_query', 'application_form_magnify',
                                          tooltip='Advanced Query'),
                       icon_button_editor('filter_by_button',
                                          'edit-find',
                                          tooltip='Filter analyses using defined criteria'),
                       icon_button_editor('graphical_filter_button',
                                          'chart_curve_go',
                                          # enabled_when='samples',
                                          tooltip='Filter analyses graphically'),
                       spring,
                       CustomLabel('datasource_url', color='maroon'),
                       spring),
                main_grp),
            handler=UnselectTabularEditorHandler(selected_name='selected_projects'))

        return v

    def _tableview_default(self):
        return Tables(model=self.model, pane=self)

    def _tabletools_default(self):
        return TableTools(model=self.model, pane=self)


        # ============= EOF =============================================
        # def _get_browser_group(self):
        # project_grp = VGroup(
        # HGroup(Label('Filter'),
        # UItem('project_filter',
        # width=75),
        # icon_button_editor('clear_selection_button',
        #                                   'cross',
        #                                   tooltip='Clear selected')),
        #         UItem('projects',
        #               editor=TabularEditor(editable=False,
        #                                    selected='selected_projects',
        #                                    adapter=ProjectAdapter(),
        #                                    multi_select=True),
        #               width=75))
        #
        #     sample_grp = VGroup(
        #         HGroup(
        #             #Label('Filter'),
        #             UItem('sample_filter_parameter',
        #                   editor=EnumEditor(name='sample_filter_parameters')),
        #             UItem('sample_filter',
        #                   width=75),
        #             UItem('sample_filter',
        #                   editor=EnumEditor(name='sample_filter_values'),
        #                   width=-25),
        #             # UItem('filter_non_run_samples',
        #             #       tooltip='Omit non-analyzed samples'),
        #             icon_button_editor('configure_sample_table',
        #                                'cog',
        #                                tooltip='Configure Sample Table')),
        #         UItem('samples',
        #               editor=TabularEditor(
        #                   adapter=self.sample_tabular_adapter,
        #                   editable=False,
        #                   selected='selected_samples',
        #                   multi_select=True,
        #                   dclicked='dclicked_sample',
        #                   column_clicked='column_clicked',
        #                   #update='update_sample_table',
        #                   #refresh='update_sample_table',
        #                   stretch_last_section=False),
        #               width=75))
        #
        #     grp = VSplit(
        #         HSplit(project_grp,
        #         sample_grp),
        #         self._get_analysis_group(),
        #         # label='Project/Sample'
        #     )
        #
        #     return grp

        # def _get_date_group(self):
        #     f_grp = HGroup(
        #         UItem('analysis_type',
        #               editor=EnumEditor(name='analysis_types')),
        #         UItem('mass_spectrometer',
        #               editor=EnumEditor(name='mass_spectrometers')),
        #         UItem('extraction_device',
        #               editor=EnumEditor(name='extraction_devices')))
        #
        #     grp = VGroup(
        #         f_grp,
        #         Heading('Start'),
        #         UItem('start_date',
        #               editor=DateEditor(allow_future=False),
        #               style='custom'),
        #         UItem('start_time', ),
        #         Item('_'),
        #         Heading('End'),
        #         UItem('end_date',
        #               editor=DateEditor(allow_future=False),
        #               style='custom'),
        #         UItem('end_time', ))
        #
        #     return VSplit(grp,
        #                   self._get_analysis_group(base='danalysis'),
        #                   label='Date')