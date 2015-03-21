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
from datetime import datetime, timedelta
import os
import urllib2
from apptools.preferences.preference_binding import bind_preference
import sys
from traits.api import HasTraits, Button, Bool, Str, Property
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.paths import r_mkdir
from pychron.updater.commit_view import CommitView, UpdateGitHistory, ManageCommitsView


class Updater(Loggable):
    check_on_startup = Bool
    branch = Str
    remote = Str
    _repo = None

    def bind_preferences(self):
        for a in ('check_on_startup', 'branch', 'remote'):
            bind_preference(self, a, 'pychron.update.{}'.format(a))

    def test_origin(self):
        if self.remote:
            return self._validate_origin(self.remote)

    def manage_version(self):
        repo = self._get_working_repo()

        # b = repo.branches[self.branch]
        # b = repo.heads[self.branch]
        # origin
        # oref = origin.refs[branchname]
        # remote_commit = oref.commit

        txt = repo.git.rev_list('origin/{}'.format(self.branch),
                                since=datetime.now() - timedelta(weeks=30),
                                branches=self.branch)
        commits = txt.split('\n')

        local_commit, remote_commit = self._get_local_remote_commits()

        self._get_selected_hexsha(commits, local_commit, remote_commit,
                                  view_klass=ManageCommitsView,
                                  auto_select=False,
                                  tags=repo.tags,

                                  # pass to model
                                  show_behind=False,)

    def check_for_updates(self, inform=False):
        branch = self.branch
        remote = self.remote
        if remote and branch:
            if self._validate_origin(remote):
                lc, rc = self._check_for_updates()
                hexsha = self._out_of_date(lc, rc)
                if hexsha:
                    origin = self._repo.remotes.origin
                    self.debug('pulling changes from {} to {}'.format(origin.url, branch))
                    origin.pull(hexsha)

                    self._build(branch, rc)
                    os.execl(sys.executable, *([sys.executable] + sys.argv))
                else:
                    if inform:
                        self.information_dialog('Application is up-to-date')
            else:
                self.warning_dialog('{} not a valid Github Repository. Unable to check for updates'.format(remote))

    # private
    def _get_dest_root(self):
        p = os.path.abspath(__file__)
        while 1:
            if os.path.basename(p) == 'Contents':
                break
            else:
                p = os.path.dirname(p)
            if len(p) == 1:
                break
        return p

    def _build(self, branch, commit):
        version = self._extract_version()
        pd = myProgressDialog(max=5200,
                              title='Builing Application. '
                                    'Version={} Branch={} ({})'.format(version, branch, commit.hexsha[:7]),
                              can_cancel=False)
        pd.open()
        pd.change_message('Building application')

        from pychron.updater.packager import make_egg, copy_resources
        # get the version number from version.py
        dest = self._get_dest_root()
        self.info('building application. version={}'.format(version))
        self.debug('building egg from {}'.format(self._repo.working_dir))
        self.debug('moving egg to {}'.format(dest))

        pd.change_message('Building Application')
        with pd.stdout():
            make_egg(self._repo.working_dir, dest, 'pychron', version)
            # build egg and move into destination
            if dest.endswith('Contents'):
                make_egg(self._repo.working_dir, dest, 'pychron', version)

                self.debug('------------- egg complete ----------------')

            pd.change_message('Copying Resources')
            if dest.endswith('Contents'):
                copy_resources()
            self.debug('------------- copy resources complete -----------')

    def _extract_version(self):
        import imp

        p = os.path.join(self._repo.working_dir, 'pychron', 'version.py')
        ver = imp.load_source('version', p)
        return ver.__version__

    def _validate_origin(self, name):
        try:
            cmd = 'https://github.com/{}'.format(name)
            urllib2.urlopen(cmd)
            return True
        except BaseException:
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
        if lc != rc:
            self.info('updates are available')
            if not self.confirmation_dialog('Updates are available. Install and Restart?'):
                return

            txt = self._repo.git.rev_list('--left-right', '{}...{}'.format(lc, rc))
            commits = [ci[1:] for ci in txt.split('\n')]
            return self._get_selected_hexsha(commits, lc, rc)

    def _get_local_remote_commits(self):

        repo = self._get_working_repo()
        branchname = self.branch
        origin = repo.remotes.origin
        origin.fetch(branchname)
        oref = origin.refs[branchname]

        remote_commit = oref.commit

        try:
            branch = getattr(repo.heads, branchname)
        except AttributeError:
            branch = repo.create_head(branchname, commit=oref.commit)

        branch.checkout()

        local_commit = branch.commit
        return local_commit, remote_commit

    def _get_selected_hexsha(self, commits, lc, rc, view_klass=None, auto_select=True,
                             tags=None, **kw):
        if view_klass is None:
            view_klass = CommitView

        lha = lc.hexsha[:7]
        rha = rc.hexsha[:7]
        ld = get_datetime(float(lc.committed_date)).strftime('%m-%d-%Y')
        rd = get_datetime(float(rc.committed_date)).strftime('%m-%d-%Y')

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
            return h.selected.hexsha

    def _get_working_repo(self):
        if not self._repo:
            from git import Repo

            p = os.path.join(paths.hidden_dir, 'updates', 'pychron')
            if not os.path.isdir(p):
                r_mkdir(p)
                url = 'https://github.com/{}.git'.format(self.remote)
                repo = Repo.clone_from(url, p)
            else:
                repo = Repo(p)
            self._repo = repo
        return self._repo

# ============= EOF =============================================



