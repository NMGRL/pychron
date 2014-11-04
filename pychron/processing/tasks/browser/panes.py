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
from traits.api import Int, Str, Instance
from traitsui.api import View, UItem, VGroup, HGroup, spring, \
    Group, Spring
from pyface.tasks.traits_dock_pane import TraitsDockPane
# from pychron.experiment.utilities.identifier import make_runid
# from traitsui.table_column import ObjectColumn
# from traitsui.list_str_adapter import ListStrAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.browser.adapters import BrowserAdapter, SampleAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.tasks.browser.sample_view import BrowserSampleView
from pychron.processing.tasks.browser.query_view import BrowserQueryView


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
                   ('EVal.', 'extract_value'),
                   ('Cleanup','cleanup'),
                   ('Dur','duration'),
                   ('Device', 'extract_device')]

    columns = [('Run ID', 'record_id'),
               ('Tag', 'tag')]

    record_id_width = Int(100)
    tag_width = Int(65)
    odd_bg_color = 'lightgray'
    font = 'arial 10'

    def get_menu(self, obj, trait, row, column):
        e=obj.append_replace_enabled
        actions = [Action(name='Unselect', action='unselect_analyses'),
                   Action(name='Replace', action='replace_items', enabled=e),
                   Action(name='Append', action='append_items', enabled=e),
                   Action(name='Open', action='recall_items'),
                   Action(name='Open Copy', action='recall_copies'),
                   Action(name='Find References', action='find_refs')]
        # if obj.id == 'pychron.recall':
        #     actions.pop(1)
        #     actions.pop(1)

        return MenuManager(*actions)

    def get_bg_color(self, obj, trait, row, column=0):
        color = 'white'
        if self.item.is_plateau_step:
            color = 'lightgreen'

        return color


class BrowserPane(TraitsDockPane):
    name = 'Browser'
    id = 'pychron.browser'
    multi_select = True
    analyses_defined = Str('1')

    sample_tabular_adapter = Instance(SampleAdapter, ())
    analysis_tabular_adapter = Instance(AnalysisAdapter, ())
    analysis_group_tabular_adapter = Instance(AnalysisGroupAdapter, ())

    sample_view = Instance(BrowserSampleView)
    query_view = Instance(BrowserQueryView)

    def _get_browser_group(self):
        grp = Group(UItem('pane.sample_view',
                          style='custom',
                          visible_when='sample_view_active'),
                    UItem('pane.query_view',
                          style='custom',
                          visible_when='not sample_view_active'))
        return grp

    def traits_view(self):
        main_grp = self._get_browser_group()

        v = View(
            VGroup(
                HGroup(
                    # icon_button_editor('advanced_query', 'application_form_magnify',
                    # tooltip='Advanced Query'),
                    icon_button_editor('filter_by_button',
                                       'find',
                                       tooltip='Filter analyses using defined criteria'),
                    icon_button_editor('graphical_filter_button',
                                       'chart_curve_go',
                                       # enabled_when='samples',
                                       tooltip='Filter analyses graphically'),
                    icon_button_editor('toggle_view',
                                       'arrow_switch',
                                       tooltip='Toggle between Sample and Time views'),
                    spring,
                    UItem('use_focus_switching',
                          tooltip='Show/Hide Filters on demand'),
                    Spring(springy=False, width=10),
                    icon_button_editor('toggle_focus',
                                       'arrow_switch',
                                       enabled_when='use_focus_switching',
                                       tooltip='Toggle Filter and Result focus'),
                    spring,
                    CustomLabel('datasource_url', color='maroon'),
                    ),
                main_grp),
            # handler=TablesHandler()
            # handler=UnselectTabularEditorHandler(selected_name='selected_projects')
        )

        return v

    def _sample_view_default(self):
        return BrowserSampleView(model=self.model, pane=self)

    def _query_view_default(self):
        return BrowserQueryView(model=self.model.data_selector, pane=self)
        # ============= EOF =============================================
        # def _get_browser_group(self):
        # project_grp = VGroup(
        # HGroup(Label('Filter'),
        # UItem('project_filter',
        # width=75),
        # icon_button_editor('clear_selection_button',
        # 'cross',
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