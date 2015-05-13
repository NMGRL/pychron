# # ===============================================================================
# # Copyright 2013 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
# from pyface.action.menu_manager import MenuManager
# from traits.api import Int, Str, Instance
# from traitsui.api import View, UItem, VGroup, HGroup, spring, \
# Group, Spring
# from pyface.tasks.traits_dock_pane import TraitsDockPane
# from traitsui.menu import Action
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# from pychron.core.ui.custom_label_editor import CustomLabel
# from pychron.envisage.browser.adapters import BrowserAdapter, LabnumberAdapter
# from pychron.envisage.icon_button_editor import icon_button_editor
# from pychron.processing.tasks.browser.sample_view import BrowserSampleView
# # from pychron.processing.tasks.browser.query_view import BrowserQueryView
# from pychron.processing.tasks.browser.time_view import TimeViewModel
#
#
# class AnalysisGroupAdapter(BrowserAdapter):
# all_columns = [('Name', 'name'),
# ('Created', 'create_date'),
#                    ('Modified', 'last_modified')]
#
#     columns = [('Name', 'name'),
#                ('Create Date', 'create_date'),
#                ('Modified', 'last_modified')]
#
#
# class BrowserPane(TraitsDockPane):
#     name = 'Browser'
#     id = 'pychron.browser'
#     multi_select = True
#     analyses_defined = Str('1')
#
#     labnumber_tabular_adapter = Instance(LabnumberAdapter, ())
#     # analysis_tabular_adapter = Instance(AnalysisAdapter, ())
#     analysis_group_tabular_adapter = Instance(AnalysisGroupAdapter, ())
#
#     sample_view = Instance(BrowserSampleView)
#     # query_view = Instance(BrowserQueryView)
#     time_view = Instance(TimeViewModel)
#
#     def _get_browser_group(self):
#         grp = Group(UItem('pane.sample_view',
#                           style='custom',
#                           visible_when='sample_view_active'),
#                     UItem('time_view_model',
#                           style='custom',
#                           visible_when='not sample_view_active')
#                     # UItem('pane.query_view',
#                     # style='custom',
#                     # visible_when='not sample_view_active')
#         )
#         return grp
#
#     def traits_view(self):
#         main_grp = self._get_browser_group()
#
#         v = View(
#             VGroup(
#                 HGroup(
#                     # icon_button_editor('advanced_query', 'application_form_magnify',
#                     # tooltip='Advanced Query'),
#                     icon_button_editor('filter_by_button',
#                                        'find',
#                                        tooltip='Filter analyses using defined criteria'),
#                     icon_button_editor('graphical_filter_button',
#                                        'chart_curve_go',
#                                        # enabled_when='samples',
#                                        tooltip='Filter analyses graphically'),
#                     icon_button_editor('toggle_view',
#                                        'arrow_switch',
#                                        tooltip='Toggle between Sample and Time views'),
#                     spring,
#                     UItem('use_focus_switching',
#                           tooltip='Show/Hide Filters on demand'),
#                     Spring(springy=False, width=10),
#                     icon_button_editor('toggle_focus',
#                                        'arrow_switch',
#                                        enabled_when='use_focus_switching',
#                                        tooltip='Toggle Filter and Result focus'),
#                     spring,
#                     # UItem('current_task_name', style='readonly'),
#                     CustomLabel('datasource_url', color='maroon'),
#                 ),
#                 main_grp),
#             # handler=TablesHandler()
#             # handler=UnselectTabularEditorHandler(selected_name='selected_projects')
#         )
#
#         return v
#
#     def _sample_view_default(self):
#         return BrowserSampleView(model=self.model, pane=self)
#
#         # def _query_view_default(self):
#         # return BrowserQueryView(model=self.model.data_selector, pane=self)
#
# # ============= EOF =============================================
