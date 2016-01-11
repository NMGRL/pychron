# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Str, Button, List
from traitsui.api import View, UItem, VGroup
# ============= standard library imports ========================
import os
import paramiko
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.progress import progress_iterator
from pychron.loggable import Loggable
from pychron.paths import paths


def database_path():
    return os.path.join(paths.dvc_dir, 'index.sqlite3')


def switch_to_offline_database(preferences):
    prefid = 'pychron.dvc.db'
    kind = '{}.kind'.format(prefid)
    path = '{}.path'.format(prefid)

    preferences.set(kind, 'sqlite')
    preferences.set(path, database_path())
    preferences.save()


class RepositoryTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Create Date', 'created_at'),
               ('Last Change', 'pushed_at')]


class WorkOffline(Loggable):
    """
    1. Select set of repositories
    2. clone repositories
    3. update the meta repo
    4. copy the central db to a sqlite db
    5. set DVC db preferences to sqlite
    """
    work_offline_user = Str
    work_offline_password = Str

    repositories = List
    selected_repositories = List

    work_offline_button = Button('Work Offline')

    def initialize(self):
        """
        check internet connection.
            a. check database
            b. check github
        """
        if self._check_database_connection():
            if self._check_github_connection():
                if self._load_preferences():
                    repos = self.dvc.remote_repositories(attributes=('name',
                                                                     'created_at',
                                                                     'pushed_at'))
                    repos = sorted([ri for ri in repos if ri.name != 'meta'],
                                   key=lambda x: x.name)
                    self.repositories = repos
                    return True

    # private
    def _load_preferences(self):
        prefs = self.application.preferences
        prefid = 'pychron.dvc'
        wou = prefs.get('{}.work_offline_user'.format(prefid))
        if wou is None:
            self.warning_dialog('No WorkOffline user set in preferences')
            return

        self.work_offline_user = wou

        wop = prefs.get('{}.work_offline_password'.format(prefid))
        if wop is None:
            self.warning_dialog('No WorkOffline password set in preferences')
            return

        self.work_offline_password = wop
        return True

    def _check_database_connection(self):
        return self.dvc.connect()

    def _check_github_connection(self):
        return self.dvc.check_github_connection()

    def _work_offline(self):
        self.debug('work offline')

        # clone repositories
        if not self._clone_repositories():
            return

        # update meta
        self.dvc.open_meta_repo()
        self.dvc.meta_pull()

        # clone central db
        if not self._clone_central_db():
            return

        msg = 'Would you like to switch to the offline database?'
        if self.confirmation_dialog(msg):
            # update DVC preferences
            self._update_preferences()

    def _clone_repositories(self):
        self.debug('clone repositories')

        # check for selected repositories
        if not self.selected_repositories:
            return

        # clone the repositories
        def func(x, prog, i, n):
            if prog is not None:
                prog.change_message('Cloning {}'.format(x.name))
            self.dvc.clone_experiment(x.name)

        progress_iterator(self.selected_repositories, func, threshold=0)

        return True

    def _clone_central_db(self):
        """
        use mysql2sqlite.sh. this script requires mysqldump so maybe not the
        best option.

        another solution is to have the server convert the database to sqlite
        then grab the sqlite file from the server

        use ssh to run mysql2sqlite.sh
        use ftp to grab the file
        """
        self.debug('clone central db')

        # dump the mysql database to sqlite
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.dvc.db.host,
                    username=self.work_offline_user,
                    password=self.work_offline_password)

        cmd = '/Users/Shared/work_offline.sh'
        stdin, stdout, stderr = ssh.exec_command(cmd)

        # fetch the sqlite file
        ftp = ssh.open_sftp()
        rp = '/Users/Shared/database.sqlite'

        ftp.get(database_path(), rp)

    def _update_preferences(self):
        self.debug('update dvc preferences')

        switch_to_offline_database(self.application.preferences)

    # handlers
    def _work_offline_button_fired(self):
        self.debug('work offline fired')
        self._work_offline()

    def traits_view(self):
        v = View(VGroup(UItem('repositories',
                              editor=TabularEditor(adapter=RepositoryTabularAdapter(),
                                                   selected='selected_repositories',
                                                   multi_select=True)),
                        UItem('work_offline_button',
                              enabled_when='selected_repositories')),
                 title='Work Offline',
                 resizable=True,
                 width=500, height=500)
        return v

# ============= EOF =============================================
