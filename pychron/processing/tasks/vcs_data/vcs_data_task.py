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
# import os
# from pyface.tasks.action.schema import SToolBar
# import apptools.sweet_pickle as pickle
# from traits.api import List, Str, Instance, Any
#
# #============= standard library imports ========================
# #============= local library imports  ==========================
# from pychron.experiment.utilities.identifier import make_runid
# from pychron.paths import paths
# from pychron.envisage.tasks.base_task import BaseManagerTask
# from pychron.processing.tasks.vcs_data.actions import CommitVCSAction, ShareVCSAction, MigrateProjectRepositoriesAction
# from pychron.processing.tasks.vcs_data.panes import VCSCentralPane
# from pychron.processing.vcs_data.diff import Diff
# from pychron.processing.vcs_data.vcs_manager import IsotopeVCSManager
#
#
# class VCSDataTask(BaseManagerTask):
#     id='pychron.processing.vcs'
#     diffs=List
#     selected_diff=Any
#
#     tool_bars = [SToolBar(
#                           CommitVCSAction(),
#                           ShareVCSAction(),
#                           MigrateProjectRepositoriesAction())]
#
#     selected_repository=Str
#     repositories=List
#     vcs=Instance(IsotopeVCSManager, ())
#
#     commit_message=Str
#     prev_commit_message=Str
#     prev_commit_messages=List
#
#     def prepare_destroy(self):
#         if self.commit_message:
#             if self._commit_messages:
#                 if not self._commit_messages[-1]==self.commit_message:
#                     self._commit_messages.append(self.commit_message)
#
#         p=os.path.join(paths.hidden_dir, 'commit_messages')
#         with open(p, 'w') as fp:
#             pickle.dump(self._commit_messages, fp)
#
#     def activated(self):
#         p = os.path.join(paths.hidden_dir, 'commit_messages')
#         self._commit_messages=[]
#         self.prev_commit_messages=[]
#
#         if os.path.isfile(p):
#             with open(p, 'r') as fp:
#                 try:
#                     ms=pickle.load(fp)
#                     self._commit_messages=ms
#
#                 except pickle.PickleError:
#                     pass
#
#         if self._commit_messages:
#
#             self.prev_commit_messages=[ci[:10] for ci in self._commit_messages]
#             self.prev_commit_message=self.prev_commit_messages[-1]
#             # self.commit_message=self._commit_messages[-1]
#
#     def _prev_commit_message_changed(self):
#         if self.prev_commit_message:
#             idx=self.prev_commit_messages.index(self.prev_commit_message)
#             self.commit_message=self._commit_messages[idx]
#
#     def create_central_pane(self):
#         return VCSCentralPane(model=self)
#
#     def create_dock_panes(self):
#         panes=[]
#         return panes
#
#     def initiate_push(self):
#         pass
#
#     def initiate_pull(self):
#         pass
#
#     def migrate_project_repositories(self):
#         """
#             utitlity function for migrating projects from mysql to git
#             create an analysis file for each analysis in the project
#         """
#         from pychron.database.isotope_database_manager import IsotopeDatabaseManager
#         src=IsotopeDatabaseManager()
#         db=src.db
#
#         with db.session_ctx():
#             projects=['Minna Bluff']
#
#             n=db.get_project_analysis_count(projects)
#             if n:
#                 prog = src.open_progress(n, close_at_end=False)
#                 for pr in projects:
#                     # self.vcs.set_repo(pr)
#                     pr=db.get_project(pr)
#                     ans=[ai for s in pr.samples
#                          for li in s.labnumbers
#                             for ai in li.analyses][:20]
#
#                     for ai in ans:
#                         ai=src.make_analysis(ai, progress=prog)
#                         try:
#                             self.vcs.add_analysis(ai, commit=False)
#                         except BaseException, e:
#                             rid=make_runid(ai.labnumber, ai.aliquot, ai.step)
#                             self.debug('Failed making {}'.format(rid, e))
#                     self.vcs.commit('{} - project migration'.format(pr.name))
#                     self.vcs.push()
#                 prog.close()
#                 self.information_dialog('Migration completed')
#
#     def share(self):
#         path = '/Users/ross/Sandbox/git/vcs_data.git'
#         url = 'file://{}'.format(path)
#
#         self.vcs.create_remote_repo(path)
#         self.vcs.create_remote(url)
#
#         self.vcs.push()
#
#     def commit(self):
#         #dont commit if there are no changes
#         if self.diffs:
#             if self.commit_message.strip():
#                 for di in self.diffs:
#                     if di.use:
#                         self.vcs.add(di.path, commit=False)
#
#                 self.vcs.commit_change(self.commit_message)
#                 self._commit_messages.append(self.commit_message)
#             else:
#                 self.information_dialog('Please enter a comment for this commit')
#         else:
#             self.information_dialog('No changes to commit')
#
#     def _selected_repository_changed(self):
#         self.diffs = []
#         self.selected_diff = Diff()
#
#         self.vcs.set_repo(self.selected_repository)
#         if self.vcs.is_dirty():
#             self.diffs = self.vcs.get_diffs()
#
#     def _repositories_default(self):
#         root = paths.vcs_dir
#         rs = [ri for ri in os.listdir(root)
#               if os.path.isdir(os.path.join(root, ri, '.git'))]
#
#         self.selected_repository = rs[0]
#         return rs
# #============= EOF ============================================= k
#
