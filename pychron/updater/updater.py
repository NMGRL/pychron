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

import os
import subprocess
import sys

import git
import requests

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from git import GitCommandError
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import information
from traits.api import Bool, Str, Directory

from pychron.core.helpers.datetime_tools import get_datetime
from pychron.git_archive.repo_manager import StashCTX
from pychron.loggable import Loggable
from pychron.paths import r_mkdir
from pychron.pychron_constants import STARTUP_MESSAGE_POSITION
from pychron.updater.commit_view import CommitView, UpdateGitHistory
from pychron.globals import globalv


def gitcommand(repo, name, tag, func):
    try:
        func()
    except GitCommandError as e:
        if e.stderr.startswith(
            "error: Your local changes to the following files would be overwritten by "
            "checkout"
        ):
            if (
                confirm(
                    None,
                    "You have local changes to Pychron that would be overwritten by {} {}"
                    "Would you like continue? If Yes you will be presented with a choice to stash "
                    "or delete your changes".format(tag, name),
                )
                == YES
            ):
                if (
                    confirm(
                        None, "Would you like to maintain (i.e. stash) your changes?"
                    )
                    == YES
                ):
                    repo.git.stash()
                    func()
                    repo.git.stash("pop")
                    return
                elif confirm(None, "Would you like to delete your changes?") == YES:
                    repo.git.checkout("--", ".")
                    func()
                    return

            information(None, '{} branch "{}" aborted'.format(tag.capitalize(), name))


class Updater(Loggable):
    check_on_startup = Bool
    check_on_quit = Bool
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
        for a in (
            "check_on_startup",
            "branch",
            "remote",
            "use_tag",
            "version_tag",
            "build_repo",
            "check_on_quit",
        ):
            bind_preference(self, a, "pychron.update.{}".format(a))

    def test_origin(self):
        if self.remote:
            return self._validate_origin(self.remote)

    def set_revisions(self):
        self.debug(
            "setting revisions from local repository. not fetching latest commit from remote"
        )
        self._get_local_remote_commits(fetch=False)

    def check_for_updates(self, inform=False, restart=True):
        self.debug("checking for updates")
        branch = self.branch
        remote = self.remote

        repo = self._get_working_repo()
        if not repo:
            self.debug("no repo")
            return

        if self.use_tag:
            # check for new tags
            self._fetch(prune=True)

            tags = repo.tags
            ctag = tags[self.version_tag]
            tags = [t for t in tags if t.tag]
            mrtag = sorted(tags, key=lambda x: x.tag.tagged_date)[-1]
            if mrtag.tag.tagged_date > ctag.tag.tagged_date:
                if self.confirmation_dialog(
                    "New release available Current:{} New: {}\nUpdate?".format(
                        ctag.name, mrtag.name
                    )
                ):
                    repo.git.fetch()
                    repo.git.checkout("-b", mrtag.name, mrtag.name)
        else:
            self.debug(f"checking for updates. branch={branch}, remote={remote}")
            if remote and branch:
                if self._validate_origin(remote):
                    if self._validate_branch(branch):
                        lc, rc = self._get_local_remote_commits()
                        hexsha = self._out_of_date(lc, rc)
                        if hexsha:
                            # tag this commit so we can easily jump back
                            # however since the update may break pychron
                            # the only reliable way to revert is using an external process
                            tagids = [
                                int(t.name.split("/")[1])
                                for t in repo.tags
                                if t.name.startswith("recovery")
                            ]
                            rid = max(tagids) + 1 if tagids else 1
                            repo.create_tag("recovery/{}".format(rid))

                            origin = repo.remotes.origin
                            self.debug(
                                "pulling changes from {} to {}".format(
                                    origin.url, branch
                                )
                            )

                            try:
                                with StashCTX(repo):
                                    gitcommand(
                                        repo,
                                        repo.head.name,
                                        "pull",
                                        lambda: repo.git.pull(origin, hexsha),
                                    )
                            except BaseException:
                                self.debug_exception()
                                self.warning_dialog(
                                    "Failed installing updates. Please contact pychron developers"
                                )
                                return

                            # conda_env = os.environ.get("CONDA_ENV")
                            # conda_distro = os.environ.get("CONDA_DISTRO")
                            #
                            # if conda_env is not None and conda_distro is not None:
                            #     try:
                            #         self._install_dependencies(conda_distro, conda_env)
                            #     except BaseException as e:
                            #         self.debug(
                            #             "Install dependencies exception={}".format(e)
                            #         )
                            #         self.debug("CONDA_DISTRO={}".format(conda_distro))
                            #         self.debug("CONDA_ENV={}".format(conda_env))
                            #         self.warning_dialog(
                            #             "Automatic installation of dependencies failed. Manual updates "
                            #             "may be required. Set CONDA_ENV and CONDA_DISTRO environment "
                            #             "variables to resolve this issue"
                            #         )
                            # self._install_dependencies_edm()

                            if os.getenv("PYCHRON_UPDATE_DATABASE", False):
                                self._update_database()

                            if restart and self.confirmation_dialog("Restart?"):
                                os.execl(sys.executable, *([sys.executable] + sys.argv))
                        elif hexsha is None:
                            if inform:
                                self.information_dialog("Application is up-to-date")
                        else:
                            self.info("User chose not to update at this time")
                else:
                    self.warning_dialog(
                        "{} not a valid Github Repository. Unable to check for updates".format(
                            remote
                        )
                    )

    def _update_database(self):
        url = os.getenv("PYCHRON_ALEMBIC_URL")
        if not url:
            self.warning_dialog(
                'Please set "PYCHRON_ALEMBIC_URL" environment variable. eg. '
                "mysql+pymysql://<user>:<pwd>@<host>/<dbname>"
            )
            return

        p = self.build_repo
        try:
            os.chdir(p)

            with open("update_alembic.ini", "w") as wfile:
                with open("update_alembic.template", "r") as rfile:
                    temp = rfile.read()
                wfile.write(temp.format(url))

            out = subprocess.check_output(
                ["alembic", "-c", "update_alembic.ini", "current"]
            )
            if b"(head)" in out:
                self.info("database is up to date")
            else:
                if self.confirmation_dialog(
                    "Database is out of date. Would you like to attempt an update?"
                ):
                    try:
                        subprocess.check_call(
                            ["alembic", "-c", "update_alembic.ini", "upgrade", "head"]
                        )
                    except subprocess.CalledProcessError:
                        self.debug_exception()
                        self.warning_dialog(
                            "Automatic database updates failed. Please consult Pychron Labs"
                        )

        except subprocess.CalledProcessError as e:
            self.warning_dialog(
                "Automatic database updates not available. Please install alembic and check "
                "PYCHRON_ALEMBIC_URL is correct"
            )

    def _install_dependencies_pip(self):
        from library_manager import LibraryManager

        lm = LibraryManager()
        lm.install_dependencies()

    def _install_dependencies_conda(self, conda_distro, conda_env):
        # install dependencies
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        binroot = os.path.join(conda_distro, "bin")
        conda = os.path.join(binroot, "conda")

        cp = os.path.join(root, "app_utils", "requirements", "conda_requirements.txt")

        args = [conda, "update", "-y", "--file={}".format(cp)]
        if conda_env:
            args.extend(("-n", conda_env))

        subprocess.call(args)
        pip = os.path.join(binroot, "pip")
        pp = os.path.join(root, "app_utils", "requirements", "pip_requirements.txt")
        subprocess.call([pip, "install", "-r", pp])

    def _fetch(self, branch=None, prune=False):
        repo = self._get_working_repo()
        if repo is not None:
            origin = repo.remotes.origin
            try:
                if prune:
                    repo.git.fetch("--prune", origin, "+refs/tags/*:refs/tags/*")

                if branch:
                    repo.git.fetch(origin, branch)
                else:
                    repo.git.fetch(origin)
            except GitCommandError as e:
                self.warning("Failed to fetch. {}".format(e))

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
            self.warning("branches do not match")
            if self.confirmation_dialog(
                "The branch specified in Preferences does not match the branch in the build directory.\n"
                "Preferences branch: {}\n"
                "Build branch: {}\n"
                "Do you want to proceed?".format(name, active_branch_name)
            ):
                self.info(
                    "switching from branch: {} to branch: {}".format(
                        active_branch_name, name
                    )
                )
                self._fetch(name)
                branch = self._get_branch(name)

                branch.checkout()

                return True
        else:
            self._fetch(name)
            return True

    def _validate_origin(self, name):
        cmd = "https://github.com/{}".format(name)
        try:
            kw = {}
            if globalv.cert_file:
                kw["verify"] = globalv.cert_file
            requests.get(cmd, **kw)
            return True
        except BaseException as e:
            print("excepiton validating origin", cmd, e)
            return

    # def _check_for_updates(self):
    #     branchname = self.branch
    #     self.debug('checking for updates on {}'.format(branchname))
    #     local_commit, remote_commit = self._get_local_remote_commits()
    #
    #     self.debug('local  commit ={}'.format(local_commit))
    #     self.debug('remote commit ={}'.format(remote_commit))
    #     self.application.set_revisions(local_commit, remote_commit)
    #     return local_commit, remote_commit

    def _out_of_date(self, lc, rc, restart=True):
        if rc and lc != rc:
            self.info("updates are available")
            msg = "Updates are available."
            if restart:
                msg = "{}. Install and Restart?".format(msg)
            else:
                msg = "{}. Install?".format(msg)

            if not self.confirmation_dialog(msg, position=STARTUP_MESSAGE_POSITION):
                return False

            txt = self._repo.git.rev_list("--left-right", "{}...{}".format(lc, rc))
            commits = [ci[1:] for ci in txt.split("\n")]
            return self._get_selected_hexsha(commits, lc, rc)

    def _get_branch(self, name):
        repo = self._get_working_repo()
        try:
            branch = getattr(repo.heads, name)
        except AttributeError:
            oref = repo.remotes.origin.refs[name]
            branch = repo.create_head(name, commit=oref.commit)
        return branch

    def _get_local_remote_commits(self, fetch=True):
        branchname = self.branch
        self.debug("checking for updates on branch={}".format(branchname))

        if self.use_tag:
            local_commit, remote_commit = (
                self._repo.tags[self.version_tag],
                self._repo[self.version_tag],
            )
            # return self.version_tag, self.version_tag
        else:
            repo = self._get_working_repo()
            if fetch:
                repo.git.fetch()

            branchname = self.branch
            if not branchname:
                branchname = repo.head.name

            origin = repo.remotes.origin
            try:
                oref = origin.refs[branchname]
                remote_commit = oref.commit
            except IndexError:
                remote_commit = None

            branch = self._get_branch(branchname)

            local_commit = branch.commit

        self.debug("local  commit ={}".format(local_commit))
        self.debug("remote commit ={}".format(remote_commit))
        self.application.set_revisions(local_commit, remote_commit)
        return local_commit, remote_commit

    def _get_local_commit(self):
        repo = self._get_working_repo()
        branchname = self.branch
        branch = getattr(repo.heads, branchname)
        return branch.commit

    def _get_selected_hexsha(
        self, commits, lc, rc, view_klass=None, auto_select=True, tags=None, **kw
    ):
        if view_klass is None:
            view_klass = CommitView

        lha = lc.hexsha[:7] if lc else ""
        rha = rc.hexsha[:7] if rc else ""
        ld = get_datetime(float(lc.committed_date)).strftime("%m-%d-%Y")

        rd = get_datetime(float(rc.committed_date)).strftime("%m-%d-%Y") if rc else ""

        n = len(commits)
        h = UpdateGitHistory(
            n=n,
            branchname=self.branch,
            local_commit="{} ({})".format(ld, lha),
            head_hexsha=lc.hexsha,
            latest_remote_commit="{} ({})".format(rd, rha),
            **kw,
        )

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

            p = self.build_repo
            if not p:
                self.information_dialog(
                    'Please set "Build Directory" in Update Preferences',
                    position=STARTUP_MESSAGE_POSITION,
                )
                return

            if not os.path.isdir(p):
                r_mkdir(p)
                if self.remote:
                    url = "https://github.com/{}.git".format(self.remote)
                    repo = Repo.clone_from(url, p)
                else:
                    self.information_dialog(
                        'Please set the Update Repo "Name" in Update Preferences',
                        position=STARTUP_MESSAGE_POSITION,
                    )
                    return
            else:
                try:
                    repo = Repo(p)
                except git.GitError as e:
                    self.information_dialog(
                        "The build directory you have selected is invalid. {}".format(
                            e
                        ),
                        position=STARTUP_MESSAGE_POSITION,
                    )
                    return

            self._repo = repo
        return self._repo

        # def _get_delete_enabled(self):
        #     return not (self.branch == self.edit_branch or self.edit_branch.startswith('origin'))


# ============= EOF =============================================
