# # ===============================================================================
# # Copyright 2019 ross
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
# import os
# import shutil
#
# import xlrd
# from pyface.constant import OK
# from pyface.file_dialog import FileDialog
#
# from pychron.core.helpers.iterfuncs import groupby_idx
# from pychron.core.utils import alpha_to_int
# from pychron.dvc import dvc_dump, analysis_path, dvc_load
# from pychron.experiment.utilities.identifier import strip_runid
# from pychron.loggable import Loggable
# from pychron.paths import paths
#
# DEBUG = os.getenv('MAP_RUNID_DEBUG', False)
#
#
# class MapRunID(Loggable):
#     def map(self, dvc):
#         if self.confirmation_dialog('''Are you sure you want to edit analysis runids? This cannot be easily undone.
# If you want to continue you will be asked to select an excel file with the following format?
#
# original_runid, new_runid
#
# e.g
# original_runid, new_runid
# 10000-01, 20000-04
# 10000-02, 20000-05
# 10000-03, 20000-06
#
#
# note: first line is ignored and can be blank or a column header'''):
#
#             path = self._get_path()
#             if os.path.isfile(path):
#                 self._map(dvc, path)
#
#     def _get_path(self):
#         dialog = FileDialog(action='open', default_directory=paths.data_dir)
#         if dialog.open() == OK:
#             r = dialog.path
#             return r
#
#     def _map(self, dvc, r):
#         try:
#             dvc.create_session()
#             if os.path.splitext(r)[-1] in ('.xls', '.xlsx'):
#                 self._map_excel(dvc, r)
#             else:
#                 self._map_csv(dvc, r)
#
#             dvc.commit()
#             dvc.close_session()
#
#         except BaseException as e:
#             self.debug_exception()
#             self.warning_dialog('Failed to map runids. error="{}"'.format(e))
#
#     def _map_csv(self, dvc, path):
#         pass
#
#     def _map_excel(self, dvc, path):
#         wb = xlrd.open_workbook(path)
#         sheet = wb.sheet_by_index(0)
#         items = []
#         for i, row in enumerate(sheet.get_rows()):
#             if i == 0:
#                 continue
#
#             src = row[0].value
#             dst = row[1].value
#
#             # get the repository for this analysis
#             reponame = dvc.get_analysis_repository(src)
#             if reponame:
#                 reponame = reponame[0]
#
#                 items.append((reponame, src, dst))
#
#         if items:
#             self._map_runids(dvc, items)
#
#     def _map_runids(self, dvc, items):
#         for repo, items in groupby_idx(items, 0):
#             # update repo
#             dvc.sync_repo(repo)
#             paths = []
#             for repo, src, dst in items:
#                 ps = self._map_runid(dvc, repo, src, dst)
#                 if not ps:
#                     return
#                 paths.extend(ps)
#
#             if paths:
#                 dvc.repository_add_paths(repo, paths)
#                 dvc.repository_commit(repo, '<MANUAL> modified RunID')
#                 if DEBUG:
#                     if not self.confirmation_dialog('Share changes?'):
#                         return
#                 dvc.push_repository(repo)
#
#     def _map_runid(self, dvc, repo, src, dst):
#         """
#
#         :param src:
#         :param dest:
#         :return:
#         """
#
#         # edit database
#         err = dvc.map_runid(src, dst)
#         if err:
#             if self.confirmation_dialog('{}. Do you want to '
#                                         'continue?'.format(err)):
#                 return
#         else:
#             # edit files
#             return self._map_paths(repo, src, dst)
#
#     def _map_paths(self, repo, src, dst):
#         root = os.path.join(paths.repository_dataset_dir, repo)
#
#         ps = []
#
#         def debug(msg, a, b):
#             self.debug('{:<20s} {:<35s} >> {}'.format(msg, os.path.relpath(a, root),
#                                                       os.path.relpath(b, root)))
#
#         sp = analysis_path(src, repo)
#         dp = analysis_path(dst, repo, mode='w')
#         ps.append(sp)
#         ps.append(dp)
#         if not os.path.isfile(sp):
#             self.warning('not a file {}'.format(sp))
#             return
#
#         dl, da, ds = strip_runid(dst)
#
#         jd = dvc_load(sp)
#         jd['identifier'] = dl
#         jd['aliquot'] = da
#         jd['increment'] = alpha_to_int(ds)
#
#         dvc_dump(jd, dp)
#
#         debug('----------', sp, dp)
#         for modifier in ('baselines', 'blanks', 'extraction',
#                          'intercepts', 'icfactors', 'peakcenter', '.data'):
#             sp = analysis_path(src, repo, modifier=modifier)
#             dp = analysis_path(dst, repo, modifier=modifier, mode='w')
#             if sp and os.path.isfile(sp):
#                 debug('{:<20s}'.format(modifier), sp, dp)
#                 ps.append(sp)
#                 ps.append(dp)
#                 shutil.move(sp, dp)
#         return ps
# # ============= EOF =============================================
