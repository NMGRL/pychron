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
from itertools import groupby
import os
import paramiko
from traits.api import Instance, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import std_dev, nominal_value
import yaml

from pychron.loggable import Loggable
from pychron.paths import r_mkdir, paths
from pychron.processing.vcs_data.repo_manager import RepoManager


class VCSManager(Loggable):
    """
         manage access to data sourced in git repos
         create local and remote repositories
    """
    #root location of all repositories
    root = Str


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
    repo_manager = Instance(RepoManager, ())

    def set_repo(self, name):
        p = os.path.join(paths.vcs_dir, name)

        #make or use existing repo
        self.init_repo(p)

        #add readme if none exists
        self.add_readme(p)

    def add_readme(self, p):
        p = os.path.join(p, 'README')
        if not os.path.isfile(p):
            with open(p, 'w') as fp:
                fp.write('README for PROJECT <{}>\n\n\n'
                         '**file created by Pychron\'s VCSManager'.format(os.path.basename(p)))

            self.repo_manager.add(p, msg='init commit')

    def init_repo(self, path, auto_add_remote=False):
        rm = self.repo_manager
        rm.add_repo(path)

        if auto_add_remote:
            host = ''

            rp = self.add_remote_repo(host, os.path.basename(path))
            rm.create_remote(host, rp)

    def add_remote_repo(self, host, name):
        #use ssh to make a new remote repo
        client = paramiko.SSHClient()

        user = ''
        pwd = ''
        client.connect(host, username=user, password=pwd)

        root = '/usr/data/pychron'
        p = '{}.git'.format(name)

        cmds = ('cd {}'.format(root),
                'mkdir {}.git'.format(name),
                'cd {}.git'.format(name),
                'git init --bare')

        cmd = ';'.join(cmds)
        client.exec_command(cmd)
        return os.path.join(root, p)

    def commit_change(self, msg):
        rm = self.repo_manager
        rm.commit(msg)

    #Isotope protocol
    def update_analyses(self, ans, msg):
        for proj, ais in self._groupby_project(ans):

            self.set_repo(proj)

            ais=list(ais)
            for ai in ais:
                self._update_analysis(ai)

            s=ans[0]
            e=ans[-1]
            self.commit_change('{} project={} {}({}) - {}({})'.format(msg, proj, s.record_id, s.sample, e.record_id, e.sample))

    def update_analysis(self, an, msg):
        self._update_analysis(an)
        self.commit_change(msg)

    def _update_analysis(self,an):
        root = self.repo_manager.root
        p = os.path.join(root, an.sample, an.labnumber)
        p = os.path.join(p, '{}.yaml'.format(an.record_id))
        d = self._generate_analysis_dict(an)
        with open(p, 'w') as fp:
            yaml.dump(d, fp, indent=4, default_flow_style=False)

        self.repo_manager.add(p, commit=False)

    def _groupby_project(self, ans):
        key = lambda x: x.project
        ans = sorted(ans, key=key)
        return groupby(ans, key=key)

    def add_analyses(self, ans):
        for proj, ais in self._groupby_project(ans):
            self.set_repo(proj)
            ais=list(ais)
            added=any([self._add_analysis(ai, commit=False) for ai in ais])
            if added:
                s=ais[0]
                e=ais[-1]
                self.repo_manager.commit('added analyses {}({}) to {}({}) to project= {}'.format(s.record_id, s.sample,
                                                                                                 e.record_id, e.sample,
                                                                                                 proj))

    def add_analysis(self, an):
        self.set_repo(an.project)
        self._add_analysis(an)

    def _add_analysis(self, an, commit=True):
        root = os.path.join(self.repo_manager.root, an.sample, an.labnumber)
        p = os.path.join(root, '{}.yaml'.format(an.record_id))
        if not os.path.isfile(p):
            #make necessary file structure
            r_mkdir(root)

            d = self._generate_analysis_dict(an)
            with open(p, 'w') as fp:
                yaml.dump(d, fp, indent=4, default_flow_style=False)

            self.repo_manager.add(p, commit=commit)
            return True

    #private
    def _generate_analysis_dict(self, ai):
        """
            convert types to float,int,dict,list, etc
        """
        d = dict([(k, getattr(ai, k)) for k in ('labnumber', 'aliquot',
                                                'step', 'timestamp', 'tag',
                                                'sample','project','material','mass_spectrometer')])

        def func(iso):
            return {'name': iso.name,
                    'detector': iso.detector,
                    'discrimination': float(iso.discrimination.nominal_value),
                    'discrimination_error': float(iso.discrimination.std_dev),
                    'ic_factor': float(iso.ic_factor.nominal_value),
                    'ic_factor_error': float(iso.ic_factor.std_dev),
                    'value':float(iso.value),
                    'error':float(iso.error),
                    'blank': float(iso.blank.value),
                    'blank_error': float(iso.blank.error),
                    'baseline': float(iso.baseline.value),
                    'baseline_error': float(iso.baseline.error),
                    'fit':iso.fit,
                    'filter_outliers':dict(iso.filter_outliers_dict),
                    }

        isos = [func(ii) for ii in ai.isotopes.itervalues()]
        d['isotopes'] = isos

        d['j']=float(ai.j.nominal_value)
        d['j_err']=float(ai.j.std_dev)

        d['constants']=ai.arar_constants.to_dict()
        d['production_ratios']=dict(ai.production_ratios)

        ifc=ai.interference_corrections
        nifc=dict()
        for k,v in ifc.iteritems():
            nifc[k]=nominal_value(v)
            nifc['{}_err'.format(k)]=float(std_dev(v))

        d['interfence_corrections']=nifc
        d['chron_segments']=[dict(zip(('power','duration','dt'), ci)) for ci in ai.chron_segments]
        d['irradiation_time']=ai.irradiation_time

        return d

#============= EOF =============================================

