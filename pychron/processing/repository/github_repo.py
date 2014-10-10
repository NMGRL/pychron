# # ===============================================================================
# # Copyright 2014 Jake Ross
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
# import os
# #============= standard library imports ========================
# #============= local library imports  ==========================
# from pychron.loggable import Loggable
# from pychron.processing.export.xml_analysis_exporter import XMLAnalysisExporter
# from pychron.processing.vcs_data.repo_manager import RepoManager
#
#
# class GithubAnalysisRepo(Loggable):
#     """
#         use this class to upload data to a github repository
#     """
#     def setup(self, rp):
#         self._repo_man=RepoManager()
#         self._repo_man.add_repo(rp)
#         self.repo_path = rp
#
#     def upload(self, record):
#         op=os.path.join(self.repo_path,
#                         '{}.xml'.format(record.record_id))
#
#         xml = XMLAnalysisExporter()
#         xml.destination.destination=op
#
#         xml.add(record)
#         xml.export()
#
#         self._repo_man.add(op)
#         self._repo_man.push()
#
#
#
#
#
#
#
# #============= EOF =============================================
#
#
#
