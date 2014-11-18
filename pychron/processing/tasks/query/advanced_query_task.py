# #===============================================================================
# # Copyright 2013 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #===============================================================================
#
# #============= enthought library imports =======================
# from traits.api import Instance, on_trait_change
# #============= standard library imports ========================
# #============= local library imports  ==========================
# from pychron.envisage.tasks.base_task import BaseManagerTask
# from pychron.processing.selection.data_selector import DataSelector
# from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
# from pychron.processing.tasks.query.panes import AdvancedQueryPane
#
#
# class AdvancedQueryTask(BaseManagerTask):
#     id='pychron.advanced_query'
#     name='Advanced Query'
#     data_selector=Instance(DataSelector)
#
#     def activated(self):
#         selector = self.manager.db.selector
#         selector.load_recent()
#
#     def prepare_destroy(self):
#         self.set_append_replace_enabled(False)
#
#     def set_append_replace_enabled(self, v):
#         self.data_selector.replace_enabled=v
#         self.data_selector.append_enabled=v
#
#     def create_central_pane(self):
#         selector = self.manager.db.selector
#         ds = DataSelector(database_selector=selector)
#         self.data_selector=ds
#         return AdvancedQueryPane(model=ds)
#
#     @on_trait_change('data_selector:selector:dclicked')
#     def _handle_dclick(self, new):
#         app = self.window.application
#         task = None
#         for win in app.windows:
#             task = win.active_task
#             if issubclass(type(task), AnalysisEditTask):
#                 break
#
#         if task:
#             task.recall(new.item)
#
#     @on_trait_change('data_selector:[append_button, replace_button]')
#     def _handle_selection(self, name, new):
#         ans=self.data_selector.selector.selected
#         if not ans:
#             return
#
#         app=self.window.application
#         ref_asked=False
#         for win in app.windows:
#             task=win.active_task
#             if not issubclass(type(task), AnalysisEditTask):
#                 continue
#
#             added = False
#             if hasattr(task, 'references_pane'):
#                 pane=task.references_pane
#                 if pane:
#                     if not ref_asked:
#                         add_to_ref=self.confirmation_dialog('Add selected analyses to References?')
#                         ref_asked = True
#
#                     if add_to_ref:
#                         added = True
#                         if name=='replace_button':
#                             pane.items=ans
#                         else:
#                             pane.items.extend(ans)
#             if not added:
#                 self._add_unknowns(task, name, ans)
#
#     def _add_unknowns(self, task, name, ans):
#         if name == 'replace_button':
#             task.replace_unkonwn_analyses(ans)
#         else:
#             task.append_unknown_analyses(ans)
#
#     def _add_to_pane(self, pane, action, items):
#         if action=='replace_button':
#             pane.items=items
#         else:
#             pane.items.extend(items)
# #============= EOF =============================================
#
#
