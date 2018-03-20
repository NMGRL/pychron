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
from apptools.preferences.preference_binding import bind_preference
from traits.api import Bool, Str, Directory

import os
import sys
import requests
from git import GitCommandError

from pychron.core.helpers.datetime_tools import get_datetime
from pychron.loggable import Loggable
from pychron.paths import build_repo
from pychron.paths import r_mkdir
from pychron.updater.commit_view import CommitView, UpdateGitHistory

CONDA_DISTRO = 'miniconda2'
CONDA_ENV = 'pychron_env'


class Updater(Loggable):
    check_on_startup = Bool
    branch = Str
    remote = Str

    use_tag = Bool
    version_tag = Str
    build_repo = Directory

    _repo = None

    @property
    def active_branch(self):
        repo = self._get_working_repo()
        return repo.active_branch.name

    def bind_preferences(self):
        for a in ('check_on_startup', 'branch', 'remote', 'use_tag', 'version_tag', 'build_repo'):
            bind_preference(self, a, 'pychron.update.{}'.format(a))

    def test_origin(self):
        if self.remote:
            return self._validate_origin(self.remote)

    def check_for_updates(self, inform=False):
        self.debug('checking for updates')
        branch = self.branch
        remote = self.remote
        if self.use_tag:
            # check for new tags
            self._fetch(prune=True)
            repo = self._repo
            if not repo:
                return

            tags = repo.tags
            ctag = tags[self.version_tag]
            tags = [t for t in tags if t.tag]
            mrtag = sorted(tags, key=lambda x: x.tag.tagged_date)[-1]
            if mrtag.tag.tagged_date > ctag.tag.tagged_date:
                if self.confirmation_dialog('New release available Current:{} New: {}\nUpdate?'.format(ctag.name,
                                                                                                       mrtag.name)):
                    repo.git.fetch()
                    repo.git.checkout('-b', mrtag.name, mrtag.name)
        else:
            if remote and branch:
                if self._validate_origin(remote):
                    if self._validate_branch(branch):
                        lc, rc = self._check_for_updates()
                        hexsha = self._out_of_date(lc, rc)
                        if hexsha:
                            origin = self._repo.remotes.origin
                            self.debug('pulling changes from {} to {}'.format(origin.url, branch))

                            self._repo.git.pull(origin, hexsha)
                            conda_env = os.environ.get('CONDA_ENV', CONDA_ENV)
                            conda_distro = os.environ.get('CONDA_DISTRO', CONDA_DISTRO)
                            try:
                                self._install_dependencies(conda_distro, conda_env)
                            except BaseException as e:
                                self.debug('Install dependencies exception={}'.format(e))
                                self.debug('CONDA_DISTRO={}'.format(conda_distro))
                                self.debug('CONDA_ENV={}'.format(conda_env))
                                self.warning_dialog('Automatic installation of dependencies failed. Manual updates '
                                                    'may be required. ')

                            if self.confirmation_dialog('Restart?'):
                                os.execl(sys.executable, *([sys.executable] + sys.argv))
                        elif hexsha is None:
                            if inform:
                                self.information_dialog('Application is up-to-date')
                        else:
                            self.info('User chose not to update at this time')
                else:
                    self.warning_dialog('{} not a valid Github Repository. Unable to check for updates'.format(remote))

    def _install_dependencies(self, conda_distro, conda_env):
        # install dependencies
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))



        if conda_env:
            conda_distro = os.path.join(conda_distro, 'envs', conda_env)

        binroot = os.path.join(os.path.expanduser('~'), conda_distro, 'bin')
        if not os.path.isdir(binroot):
            binroot = os.path.join(os.path.sep, conda_distro, 'bin')

        conda = os.path.join(binroot, 'conda')
        cp = os.path.join(root, 'app_utils', 'requirements', 'conda_requirements.txt')

        args = [conda, 'update', '-y', '--file={}'.format(cp)]
        if conda_env:
            args.extend(('-n', conda_env))

        subprocess.call(args)
        pip = os.path.join(binroot, 'pip')
        pp = os.path.join(root, 'app_utils', 'requirements', 'pip_requirements.txt')
        subprocess.call([pip, 'install', '-r', pp])

    def _fetch(self, branch=None, prune=False):
        repo = self._get_working_repo()
        if repo is not None:
            origin = repo.remotes.origin
            try:
                if prune:
                    repo.git.fetch('--prune', origin, '+refs/tags/*:refs/tags/*')

                if branch:
                    repo.git.fetch(origin, branch)
                else:
                    repo.git.fetch(origin)
            except GitCommandError as e:
                self.warning('Failed to fetch. {}'.format(e))

    def _validate_branch(self, name):
        """
        check that the repo's branch is name

        if not ask user if its ok to checkout branch
        :param name:
        :return:
        """

        repo = self._get_working_repo()
        active_branch_name = repo.active_branch.name
        if active_branch_name != name:
            self.warning('branches do not match')
            if self.confirmation_dialog(
                    'The branch specified in Preferences does not match the branch in the build directory.\n'
                    'Preferences branch: {}\n'
                    'Build branch: {}\n'
                    'Do you want to proceed?'.format(name, active_branch_name)):
                self.info('switching from branch: {} to branch: {}'.format(active_branch_name, name))
                self._fetch(name)
                branch = self._get_branch(name)

                branch.checkout()

                return True
        else:
            self._fetch(name)
            return True

    def _validate_origin(self, name):
        try:
            cmd = 'https://github.com/{}'.format(name)
            # six.moves.urllib.request.urlopen(cmd)
            requests.get(cmd)
            return True
        except BaseException as e:
            print('excepiton validating origin', cmd, e)
            return

    def _check_for_updates(self):
        branchname = self.branch
        self.debug('checking for updates on {}'.format(branchname))
        local_commit, remote_commit = self._get_local_remote_commits()

        self.debug('local  commit ={}'.format(local_commit))
        self.debug('remote commit ={}'.format(remote_commit))
        self.application.set_revisions(local_commit, remote_commit)
        return local_commit, remote_commit

    def _out_of_date(self, lc, rc):
        if rc and lc != rc:
            self.info('updates are available')
            if not self.confirmation_dialog('Updates are available. Install and Restart?'):
                return False

            txt = self._repo.git.rev_list('--left-right', '{}...{}'.format(lc, rc))
            commits = [ci[1:] for ci in txt.split('\n')]
            return self._get_selected_hexsha(commits, lc, rc)

    def _get_branch(self, name):
        repo = self._get_working_repo()
        try:
            branch = getattr(repo.heads, name)
        except AttributeError:
            oref = repo.remotes.origin.refs[name]
            branch = repo.create_head(name, commit=oref.commit)
        return branch

    def _get_local_remote_commits(self):
        if self.use_tag:
            return self._repo.tags[self.version_tag], self._repo[self.version_tag]
            # return self.version_tag, self.version_tag
        else:
            repo = self._get_working_repo()
            branchname = self.branch
            origin = repo.remotes.origin
            try:
                oref = origin.refs[branchname]
                remote_commit = oref.commit
            except IndexError:
                remote_commit = None

            branch = self._get_branch(branchname)

            local_commit = branch.commit
            return local_commit, remote_commit

    def _get_local_commit(self):
        repo = self._get_working_repo()
        branchname = self.branch
        branch = getattr(repo.heads, branchname)
        return branch.commit

    def _get_selected_hexsha(self, commits, lc, rc, view_klass=None, auto_select=True,
                             tags=None, **kw):
        if view_klass is None:
            view_klass = CommitView

        lha = lc.hexsha[:7] if lc else ''
        rha = rc.hexsha[:7] if rc else ''
        ld = get_datetime(float(lc.committed_date)).strftime('%m-%d-%Y')

        rd = get_datetime(float(rc.committed_date)).strftime('%m-%d-%Y') if rc else ''

        n = len(commits)
        h = UpdateGitHistory(n=n, branchname=self.branch,
                             local_commit='{} ({})'.format(ld, lha),
                             head_hexsha=lc.hexsha,
                             latest_remote_commit='{} ({})'.format(rd, rha),
                             **kw)

        repo = self._repo
        commits = [repo.commit(i) for i in commits]
        h.set_items(commits, auto_select=auto_select)
        if tags:
            h.set_tags(tags)

        cv = view_klass(model=h)
        info = cv.edit_traits()
        if info.result:
            if h.selected:
                return h.selected.hexsha

    def _get_working_repo(self):
        if not self._repo:
            from git import Repo

            p = build_repo
            if not os.path.isdir(p):
                r_mkdir(p)
                if self.remote:
                    url = 'https://github.com/{}.git'.format(self.remote)
                    repo = Repo.clone_from(url, p)
                else:
                    self.information_dialog('Please set "remote" in Updater preferences')
                    return
            else:
                repo = Repo(p)
            self._repo = repo
        return self._repo

        # def _get_delete_enabled(self):
        #     return not (self.branch == self.edit_branch or self.edit_branch.startswith('origin'))

# ============= EOF =============================================
