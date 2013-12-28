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
import os
import paramiko
from traits.api import Instance
#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.loggable import Loggable
from pychron.paths import r_mkdir
from pychron.processing.vcs_data.repo_manager import RepoManager


class VCSManager(Loggable):
    """
         manage access to data sourced in git repos
         create local and remote repositories
    """
    pass


class IsotopeVCSManager(VCSManager):
    """
        add analyses to local repository
            create a line-oriented file for each analysis
            repo organization
                -project
                 -.git
                 -sample
                  -labnumber
                   -<record_id>.yaml

        track changes
        push changes to remote repo

    """
    repo_manager=Instance(RepoManager, ())

    def init_repo(self, path, auto_add_remote=False):
        rm=self.repo_manager
        rm.add_repo(path)
        if auto_add_remote:
            host = ''

            rp=self.add_remote_repo(host, os.path.basename(path))
            rm.create_remote(host, rp)

    def add_remote_repo(self, host, name):
        #use ssh to make a new remote repo
        client = paramiko.SSHClient()

        user=''
        pwd=''
        client.connect(host, username=user, password=pwd)

        root='/usr/data/pychron'
        p='{}.git'.format(name)

        cmds=('cd {}'.format(root),
              'mkdir {}.git'.format(name),
              'cd {}.git'.format(name),
              'git init --bare')

        cmd=';'.join(cmds)
        client.exec_command(cmd)
        return os.path.join(root, p)

    def commit_change(self, msg):
        rm=self.repo_manager
        rm.commit(msg)

    def add_analyses(self, ans):
        for ai in ans:
            self._add_analysis(ai)

    def add_analysis(self, an):
        self._add_analysis(an)

    def _add_analysis(self, an):
        d=self._generate_analysis_dict(an)

        #make necessary file structure

        root = self.repo_manager.root
        p = os.path.join(root, an.sample, an.labnumber)
        r_mkdir(p)

        p = os.path.join(p, '{}.yaml'.format(an.record_id))
        if not os.path.isfile(p):
            with open(p, 'w') as fp:
                yaml.dump(d, fp)

            self.repo_manager.add(p)

    def _generate_analysis_dict(self, ai):

        d=dict([(k, getattr(ai, k)) for k in ('labnumber','aliquot','step','timestamp')])

        isos = []
        for iso in ai.isotopes.itervalues():
            i = {'name': iso.name,
                 'detector': iso.detector,
                 'discrimination': iso.discrimination.nominal_value,
                 'discrimination_error': iso.discrimination.std_dev,
                 #'data': iso.pack(),
                 'blank':iso.blank.value,
                 'blank_error':iso.blank.error,
                 'baseline':iso.baseline.value,
                 'baseline_error':iso.baseline.error,
                 }
            isos.append(i)

        d['isotopes'] = isos

        return d
#============= EOF =============================================

