#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Int, Str, Instance
from traitsui.api import View, Item, UItem, VGroup, HGroup, Label, spring, \
    VSplit, TabularEditor, EnumEditor, DateEditor, Heading
from pyface.tasks.traits_dock_pane import TraitsDockPane
# from pychron.experiment.utilities.identifier import make_runid
# from traitsui.table_column import ObjectColumn
# from traitsui.list_str_adapter import ListStrAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.browser.adapters import BrowserAdapter, SampleAdapter, ProjectAdapter
from pychron.processing.tasks.analysis_edit.panes import icon_button_editor
from pychron.core.ui.tabular_editor import myTabularEditor


class AnalysisAdapter(BrowserAdapter):
    all_columns = [('Run ID', 'record_id'),
                   ('Tag', 'tag'),
                   ('Iso Fits', 'iso_fit_status'),
                   ('Blank', 'blank_fit_status'),
                   ('IC', 'ic_fit_status'),
                   ('Flux', 'flux_fit_status')]

    columns = [('Run ID', 'record_id'),
               ('Tag', 'tag'),
               #('Iso Fits', 'iso_fit_status'),
               #('Blank', 'blank_fit_status'),
               #('IC', 'ic_fit_status'),
               #('Flux', 'flux_fit_status')
    ]

    record_id_width = Int(100)
    tag_width = Int(65)
    odd_bg_color = 'lightgray'
    font = 'arial 10'

    def get_bg_color( self, object, trait, row, column = 0):
        color = 'white'
        if self.item.is_plateau_step:
            color='lightgreen'

        return color


class BrowserPane(TraitsDockPane):
    name = 'Browser'
    id = 'pychron.browser'
    multi_select = True
    analyses_defined = Str('1')

    sample_tabular_adapter = Instance(SampleAdapter, ())
    analysis_tabular_adapter = Instance(AnalysisAdapter, ())

    def _get_browser_group(self):
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
                # UItem('filter_non_run_samples',
                #       tooltip='Omit non-analyzed samples'),
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
            self._get_analysis_group(),
            # label='Project/Sample'
        )

        return grp

    def _get_date_group(self):
        f_grp = HGroup(
            UItem('analysis_type',
                  editor=EnumEditor(name='analysis_types')),
            UItem('mass_spectrometer',
                  editor=EnumEditor(name='mass_spectrometers')),
            UItem('extraction_device',
                  editor=EnumEditor(name='extraction_devices')))

        grp = VGroup(
            f_grp,
            Heading('Start'),
            UItem('start_date',
                  editor=DateEditor(allow_future=False),
                  style='custom'),
            UItem('start_time', ),
            Item('_'),
            Heading('End'),
            UItem('end_date',
                  editor=DateEditor(allow_future=False),
                  style='custom'),
            UItem('end_time', ))

        return VSplit(grp,
                      self._get_analysis_group(base='danalysis'),
                      label='Date')

    def _get_analysis_group(self, base='analysis'):
        def make_name(name):
            return 'object.{}_table.{}'.format(base, name)

        analysis_grp = VGroup(
            HGroup(
                #Label('Filter'),
                UItem(make_name('analysis_filter_parameter'),
                      editor=EnumEditor(name=make_name('analysis_filter_parameters'))),
                UItem(make_name('analysis_filter_comparator')),
                UItem(make_name('analysis_filter'),
                      width=75),
                UItem(make_name('analysis_filter'),
                      editor=EnumEditor(name=make_name('analysis_filter_values')),
                      width=-25),
                icon_button_editor(make_name('configure_analysis_table'), 'cog',
                                   tooltip='Configure/Advanced query')),
            UItem(make_name('analyses'),
                  editor=myTabularEditor(
                      adapter=self.analysis_tabular_adapter,
                      #                                                       editable=False,
                      operations=['move'],
                      refresh=make_name('refresh_needed'),
                      selected=make_name('selected'),
                      dclicked=make_name('dclicked'),
                      multi_select=self.multi_select,
                      drag_external=True,
                      scroll_to_row=make_name('scroll_to_row'),
                      stretch_last_section=False),
                  #                                  editor=ListStrEditor(editable=False,
                  #                                           selected='selected_analysis'
                  #                                           )
                  width=300),
            HGroup(
                # Item(make_name('page_width'),
                #      label='N',
                #      tooltip='Page Width. Number of analyses to display per page'),
                #
                spring,
                #
                # icon_button_editor(make_name('backward'),
                #                    'control_rewind',
                #                    #enabled_when=make_name('backward_enabled'),
                #                    tooltip='Backward one page'),
                # icon_button_editor(make_name('forward'),
                #                    'control_fastforward',
                #                    #enabled_when=make_name('forward_enabled'),
                #                    tooltip='Forwad 1 page'),
                # UItem(make_name('page'),
                #       tooltip='Current page'),
                # UItem(make_name('npages'),
                #       format_str='%02i', style='readonly'),
                Item(make_name('omit_invalid'))
            ),
            defined_when=self.analyses_defined,
        )
        return analysis_grp

    def traits_view(self):
        # main_grp= Group(
        #     self._get_browser_group(),
        #     self._get_date_group(),
        #     layout='tabbed')

        main_grp= self._get_browser_group()

        v = View(
            VGroup(
                HGroup(icon_button_editor('advanced_query', 'application_form_magnify',
                                          tooltip='Advanced Query'),
                       spring,
                       CustomLabel('datasource_url', color='maroon'),
                       spring),
                main_grp))

        return v


#============= EOF =============================================
