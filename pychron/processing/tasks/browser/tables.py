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
from traitsui.api import View, Item, HGroup,UItem, VGroup, EnumEditor, HSplit, TabularEditor, spring, Group, Heading
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.qt.tabular_editor import UnselectTabularEditorHandler
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.tasks.browser.pane_model_view import PaneModelView


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


class Tables(PaneModelView):
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


class TableTools(PaneModelView):
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
                                       tooltip='Clear Sample Table'))
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

#============= EOF =============================================



