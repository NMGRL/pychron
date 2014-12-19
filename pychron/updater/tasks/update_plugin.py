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
import json
import urllib2
from traits.api import List, on_trait_change
from envisage.plugin import Plugin
# ============= standard library imports ========================
import stat
import os
# ============= local library imports  ==========================
from pychron import version
from pychron.applications.util.installer import Builder
from pychron.core.helpers.filetools import to_bool, remove_extension
from pychron.core.helpers.logger_setup import new_logger
from pychron.loggable import confirmation_dialog
from pychron.paths import paths, r_mkdir
from pychron.updater.tasks.update_preferences import UpdatePreferencesPane

logger = new_logger('UpdatePlugin')


def gen_commits(log):
    def _gen():
        lines = iter(log.split('\n'))
        commit = None
        while 1:
            try:
                if not commit:
                    commit = lines.next()

                author = lines.next()
                date = lines.next()
                message = []
                while 1:
                    line = lines.next()

                    if line.startswith('commit '):
                        commit = line
                        yield date, author, '\n'.join(message)
                        break
                    else:
                        if line.strip():
                            message.append(line.strip())

            except StopIteration:

                yield date, author, '\n'.join(message)
                break

    return _gen()


class UpdatePlugin(Plugin):
    name = 'Update'
    id = 'pychron.update'

    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(contributes_to='envisage.ui.tasks.preferences_panes')

    _build_required = False

    def check(self):
        try:
            from git import Repo

            return True
        except ImportError:
            return False

    def stop(self):
        logger.debug('stopping update plugin')
        if self._build_required:
            logger.debug('building new version')
            dest = self._build_update()
            if dest:
                # get executable
                mos = os.path.join(dest, 'MacOS')
                for p in os.listdir(mos):
                    if p != 'python':
                        pp = os.path.join(mos, p)
                        if stat.S_IXUSR & os.stat(pp)[stat.ST_MODE]:
                            os.execl(pp)

    def start(self):
        logger.debug('starting update plugin')
        pref = self.application.preferences
        # print pref.get('pychron.update.check_on_startup')
        if to_bool(pref.get('pychron.update.check_on_startup')):
            url = pref.get('pychron.update.remote')
            branch = pref.get('pychron.update.branch')
            if url and branch:
                self._check_for_updates(url, branch)

                # if url:
                # else:
                #     self._load_local_revision()
                # else:
                #     self._load_local_revision()

    def _load_local_revision(self):
        repo = self._get_local_repo()
        try:
            commit = repo.head.commit
        except ValueError:
            commit = None

        self.application.set_revisions(commit,
                                       'No info. available')

    def _check_for_updates(self, name, branch):
        url = 'https://github.com/{}.git'.format(name)
        remote = 'origin'
        repo = self._setup_repo(url, remote=remote)
        # return
        logger.debug('pulling changes')
        print repo
        print repo.heads
        print repo.remotes
        print repo.remotes.origin.url

        origin =repo.remotes.origin
        print origin.fetch()

        # origin = repo.remote(remote)
        # if not repo.heads:
            # repo = repo.clone(url)
            # if self._out_of_date():
            #     print repo
                # repo.che
                # origin.pull(branch)
        # else:
        #     print repo.heads
        #     branch = getattr(repo.heads, branch)
        #     branch.checkout()
            # info = origin.fetch()
            # if info:
            #     info = info[0]
            #     logger.debug('local  commit ={}'.format(repo.head.commit))
            #     logger.debug('remote commit ={}'.format(info.commit))
            #     # self.application.set_revisions(repo.head.commit,
            #     #                                info.commit)
            #     if info.commit != repo.head.commit:
            #         self._load_available_changes(repo)
            #         if self._out_of_date():
            #
            #             # for debug dont pull changes
            #             # ===========================
            #             # origin.pull('master')
            #             # ===========================
            #
            #             if confirmation_dialog('Restarted required for changes to take affect. Restart now?'):
            #                 self._build_required = True
            #                 logger.debug('Restarting')

    # def _check_for_updates(self, url):
    #     branch = 'master'
    #     remote = 'origin'
    #     repo = self._setup_repo(url, remote=remote)
    #     logger.debug('pulling changes')
    #     origin = repo.remote(remote)
    #
    #     if not repo.heads:
    #         if self._out_of_date():
    #             origin.pull(branch)
    #     else:
    #         info = origin.fetch()
    #         if info:
    #             info = info[0]
    #             logger.debug('local  commit ={}'.format(repo.head.commit))
    #             logger.debug('remote commit ={}'.format(info.commit))
    #             self.application.set_revisions(repo.head.commit,
    #                                            info.commit)
    #             if info.commit != repo.head.commit:
    #                 self._load_available_changes(repo)
    #                 if self._out_of_date():
    #
    #                     # for debug dont pull changes
    #                     # ===========================
    #                     # origin.pull('master')
    #                     # ===========================
    #
    #                     if confirmation_dialog('Restarted required for changes to take affect. Restart now?'):
    #                         self._build_required = True
    #                         logger.debug('Restarting')
    #
    # @on_trait_change('application:application_initialized')
    # def _application_initialized(self):
    #     if self._build_required:
    #         logger.debug('exit application')
    #         self.application.exit(force=True)
    #
    # private
    def _load_available_changes(self, repo):
        log = repo.git.log('HEAD..FETCH_HEAD')
        self.application.set_changes(list(gen_commits(log)))
        # for line in log.split('\n'):
        #     if
    #
    # def _build_update(self):
    #     """
    #         build egg
    #         copy egg and resources
    #     """
    #     # get the destination by walking up from __file__ until we hit pychron.app/Contents
    #     # dont build if can't find dest
    #     dest = self._get_destination()
    #     if dest:
    #         ver = version.__version__
    #         logger.info('Building {} egg for application'.format(ver))
    #
    #         builder = Builder()
    #
    #         builder.launcher_name = 'pyexperiment'
    #         builder.root = self._get_working_directory()
    #         builder.dest = dest
    #         builder.version = ver
    #
    #         logger.debug('dest={}'.format(builder.dest))
    #         logger.debug('root={}'.format(builder.root))
    #         builder.run()
    #     return dest
    #
    def _out_of_date(self):
        logger.info('updates are available')
        if confirmation_dialog('Updates are available. Would you like to install'):
            return True

    def _setup_repo(self, url, remote='origin'):
        repo = self._get_local_repo(url)
        # _remote = repo.remote(remote)
        # print type(_remote), 'dfafdsf'
        # if _remote is None:
        #     repo.create_remote(remote, url)
        # else:
        #     try:
        #         if _remote.url != url:
        #             _remote.url = url
        #     except BaseException:
        #         pass

        return repo

    def _get_local_repo(self, url):
        from git import Repo
        p = self._get_working_directory()

        if not os.path.isdir(p):
            r_mkdir(p)
            repo = Repo.clone_from(url, p)
        else:
            repo = Repo(p)
        return repo
    #
    # def _get_destination(self):
    #     """
    #         walk up from current file
    #         looking for .app
    #
    #         return .../name.app/Contents or None
    #     """
    #
    #     p = __file__
    #     while p:
    #         if p.endswith('.app'):
    #             d = os.path.join(p, 'Contents')
    #             if os.path.isdir(d):
    #                 return d
    #         p = os.path.dirname(p)
    #
    def _get_working_directory(self):
        # p = '/Users/ross/Sandbox/updater_test/user_repo'
        # if not os.path.isdir(p):
        p = os.path.join(paths.hidden_dir, 'updates', 'pychron')
        return p

    def _preferences_panes_default(self):
        return [UpdatePreferencesPane]

# ============= EOF =============================================

