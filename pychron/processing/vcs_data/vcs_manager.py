# # ===============================================================================
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
# # ===============================================================================
#
# # ============= enthought library imports =======================
# from itertools import groupby
# import os
# import subprocess
# from git.exc import GitCommandError
# import paramiko
# from traits.api import Instance, Str
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# from uncertainties import std_dev, nominal_value
# import yaml
#
# from pychron.loggable import Loggable
# from pychron.paths import r_mkdir, paths
# from pychron.processing.vcs_data.diff import Diff
# from pychron.processing.vcs_data.repo_manager import RepoManager
#
#
# class VCSManager(Loggable):
#     """
#          manage access to data sourced in git repos
#          create local and remote repositories
#     """
#     #root location of all repositories
#     root = Str
#     remote_template=Str('file:///Users/ross/Sandbox/git/{}.git')
#
# class IsotopeVCSManager(VCSManager):
#     """
#         add analyses to local repository
#             create a line-oriented file for each analysis
#             repo organization
#                 -project
#                  -.git
#                  -sample
#                   -labnumber
#                    -<record_id>.yaml
#
#         track changes
#         push changes to remote repo
#
#     """
#     repo_manager = Instance(RepoManager, ())
#
#     def is_dirty(self):
#         rm=self.repo_manager
#         return rm.is_dirty()
#
#     def get_untracked(self):
#         rm=self.repo_manager
#         return rm.get_untracked()
#
#     def get_diffs(self):
#         rm = self.repo_manager
#
#         ds=[]
#
#         diffs, patches=rm.get_local_changes()
#         for di, p in zip(diffs, patches):
#             ds.append(Diff(name=os.path.basename(di.a_blob.path),
#                            path=di.a_blob.path,
#                            patch=p,
#                            use=True))
#
#         return ds
#
#     def set_repo(self, name):
#         name=name.replace(' ','_')
#         p = os.path.join(paths.vcs_dir, name)
#
#         #make or use existing repo
#         self.init_repo(p)
#
#         #add readme if none exists
#         self.add_readme(p)
#
#     def add_readme(self, p):
#         p = os.path.join(p, 'README')
#         if not os.path.isfile(p):
#             with open(p, 'w') as fp:
#                 fp.write('README for PROJECT <{}>\n\n\n'
#                          '**file created by Pychron\'s VCSManager'.format(os.path.basename(p)))
#
#             self.repo_manager.add(p, msg='init commit')
#
#     def init_repo(self, path):
#         """
#             return if repositories already existed
#         """
#         rm = self.repo_manager
#         return rm.add_repo(path)
#
#     def create_remote(self, *args, **kw):
#         """
#             add remote url alias
#         """
#         rm=self.repo_manager
#         rm.create_remote(*args,**kw)
#
#     # def remote_repo_exists(self, path, host='localhost'):
#     #     if host == 'localhost':
#     #         return os.path.isdir(path)
#     #     else:
#     #         client = paramiko.SSHClient()
#     #         # client.connect(host, username=user, password=pwd)
#     #         stdin, stdout, stderr = client.exec_command('cd {}'.format(path))
#     #         return not 'No such file or directory' in stdout.readall()
#
#     def create_remote_repo(self, name, host='localhost'):
#         """
#             create a bare repo on the server
#         """
#         path=self.remote_template.format(name)[7:]
#         print path, host
#         if host=='localhost':
#
#             if not os.path.isdir(path):
#                 os.mkdir(path)
#                 subprocess.call(['git','--bare', 'init',path])
#         else:
#
#             client = paramiko.SSHClient()
#             # client.connect(host, username=user, password=pwd)
#
#             stdin, stdout, stderr=client.exec_command('mkdir {}'.format(path))
#             if not 'File exists' in stdout.readall():
#                 client.exec_command('git --bare init {}'.format(path))
#
#     def add(self, p, **kw):
#         rm = self.repo_manager
#         rm.add(p, **kw)
#
#     def push(self, **kw):
#         self.debug('pushing')
#         rm=self.repo_manager
#         rm.push(**kw)
#
#     def pull(self, **kw):
#         rm = self.repo_manager
#         rm.pull(**kw)
#
#     def commit(self, msg):
#         rm = self.repo_manager
#         rm.commit(msg)
#
#     #Isotope protocol
#     def clone_project_repos(self, rs):
#         for ri in rs:
#             ri=ri.replace(' ','_')
#             p=os.path.join(paths.vcs_dir, ri)
#             if not self.init_repo(p):
#                 self.debug('Cloning repository {}'.format(ri))
#
#                 url=self.remote_template.format(ri)
#                 self.create_remote(url)
#
#                 self.add_readme(p)
#                 try:
#                     self.pull(handled=False)
#                 except GitCommandError:
#                     p=os.path.basename(p)
#                     self.create_remote_repo(p)
#
#                 self.push()
#
#             self.pull()
#
#     def update_analyses(self, ans, msg):
#         for proj, ais in self._groupby_project(ans):
#
#             self.set_repo(proj)
#
#             ais=list(ais)
#             for ai in ais:
#                 self._update_analysis(ai)
#
#             s=ans[0]
#             e=ans[-1]
#             self.commit('{} project={} {}({}) - {}({})'.format(msg, proj, s.record_id, s.sample, e.record_id, e.sample))
#
#     def update_analysis(self, an, msg):
#         self._update_analysis(an)
#         self.commit(msg)
#
#     def _update_analysis(self,an):
#         root = self.repo_manager.root
#         p = os.path.join(root, an.sample, an.labnumber)
#         p = os.path.join(p, '{}.yaml'.format(an.record_id))
#         d = self._generate_analysis_dict(an)
#         with open(p, 'w') as fp:
#             yaml.dump(d, fp, indent=4, default_flow_style=False)
#
#         self.repo_manager.add(p, commit=False)
#
#     def _groupby_project(self, ans):
#         key = lambda x: x.project
#         ans = sorted(ans, key=key)
#         return groupby(ans, key=key)
#
#     def add_analyses(self, ans, **kw):
#         for proj, ais in self._groupby_project(ans):
#             self.set_repo(proj)
#             ais=list(ais)
#             added=any([self._add_analysis(ai, commit=False, **kw) for ai in ais])
#             if added:
#                 s=ais[0]
#                 e=ais[-1]
#                 self.repo_manager.commit('added analyses {}({}) to {}({}) to project= {}'.format(s.record_id, s.sample,
#                                                                                                  e.record_id, e.sample,
#                                                                                                  proj))
#
#     def add_analysis(self, an, set_repo=True, **kw):
#         if set_repo:
#             self.set_repo(an.project)
#         self._add_analysis(an, **kw)
#
#     def _add_analysis(self, an, commit=True, progress=None):
#         root = os.path.join(self.repo_manager.root, an.sample, an.labnumber)
#         p = os.path.join(root, '{}.yaml'.format(an.record_id))
#         if not os.path.isfile(p):
#             if progress:
#                 progress.change_message('Adding vcs analysis {}'.format(an.record_id))
#             #make necessary file structure
#             r_mkdir(root)
#
#             d = self._generate_analysis_dict(an)
#             with open(p, 'w') as fp:
#                 yaml.dump(d, fp, indent=4, default_flow_style=False)
#
#             self.repo_manager.add(p, commit=commit)
#             return True
#
#     #private
#     def _generate_analysis_dict(self, ai):
#         """
#             convert types to float,int,dict,list, etc
#         """
#         d = dict([(k, getattr(ai, k)) for k in ('labnumber', 'aliquot',
#                                                 'step', 'timestamp', 'tag',
#                                                 'sample','project','material','mass_spectrometer')])
#
#         def func(iso):
#             return {'name': iso.name,
#                     'detector': iso.detector,
#                     'discrimination': float(iso.discrimination.nominal_value),
#                     'discrimination_err': float(iso.discrimination.std_dev),
#                     'ic_factor': float(iso.ic_factor.nominal_value),
#                     'ic_factor_err': float(iso.ic_factor.std_dev),
#                     'value':float(iso.value),
#                     'error':float(iso.error),
#                     'blank': float(iso.blank.value),
#                     'blank_err': float(iso.blank.error),
#                     'baseline': float(iso.baseline.value),
#                     'baseline_err': float(iso.baseline.error),
#                     'fit':iso.fit,
#                     'filter_outliers':dict(iso.filter_outliers_dict),
#                     'data':iso.pack()
#                     }
#
#         isos = [func(ii) for ii in ai.isotopes.itervalues()]
#         d['isotopes'] = isos
#
#         d['j']=float(ai.j.nominal_value)
#         d['j_err']=float(ai.j.std_dev)
#
#         d['constants']=ai.arar_constants.to_dict()
#         d['production_ratios']=dict(ai.production_ratios)
#
#         ifc=ai.interference_corrections
#         nifc=dict()
#         for k,v in ifc.iteritems():
#             nifc[k]=nominal_value(v)
#             nifc['{}_err'.format(k)]=float(std_dev(v))
#
#         d['interference_corrections']=nifc
#         d['chron_segments']=[dict(zip(('power','duration','dt'), ci)) for ci in ai.chron_segments]
#         d['irradiation_time']=ai.irradiation_time
#
#         return d
#
# # ============= EOF =============================================
#
