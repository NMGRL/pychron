# ===============================================================================
# Copyright 2015 Jake Ross
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
import os
import subprocess

from git import Repo
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.loggable import Loggable
from pychron.paths import paths


def get_rsync_command(push, **kw):
    remote = kw.get('remote')
    ssh_port = kw.get('port')
    ssh_user = kw.get('user')
    options = kw.get('options')
    cmd = ['rsync', '--from0', '--files-from=-']
    rshopts = []
    for v, f in ((ssh_user, '-l'), (ssh_port, '-p')):
        if v:
            rshopts.append(f)
            rshopts.append(v)
    if rshopts:
        cmd.append('--rsh=ssh {}'.format(' '.join(rshopts)))
    if options:
        cmd.extend(options.split(' '))

    src = './'
    dest = '{}/'.format(remote)
    if push:
        cmd.append(src)
        cmd.append(dest)
    else:
        cmd.append(dest)
        cmd.append(src)

    return cmd


def rsync_pull(paths, **kw):
    return _rsync(False, paths, **kw)


def rsync_push(paths, **kw):
    return _rsync(True, paths, **kw)


def _rsync(paths, **kw):
    cmd = get_rsync_command(**kw)

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(input='\x00'.join(paths))


class DVC(Loggable):
    db = Instance('pychron.dvc.dvc_database.DVCDatabase')
    meta_repo = Instance('pychron.dvc.meta_repo.MetaRepo')
    clear_db = False
    auto_add = True

    def synchronize(self):
        """
        pull meta_repo changes

        rsync the database
        :return:
        """
        self.meta_repo.pull()
        rsync_pull()

    def commit_db(self, msg=None):
        pass
        # path, _ = os.path.splitext(self.db.path)
        # path = '{}.sql'.format(path)
        # with open(path, 'w') as wfile:
        # wfile.write(subprocess.check_output(['sqlite3',self.db.path,'.dump']))
        # path = self.db.path
        # # self.meta_repo.add(path, commit=False)
        # if msg is None:
        # msg = 'updated database'
        # try:
        # self.meta_repo.shell('update_index', '--assume-unchanged', path)
        # except:
        #     self.meta_repo.add(path, commit=False)
        #
        # self.meta_repo.commit(msg)

    def session_ctx(self):
        return self.db.session_ctx()

    def _db_default(self):
        return DVCDatabase(clear=self.clear_db, auto_add=self.auto_add)

    def _meta_repo_default(self):
        return MetaRepo(auto_add=self.auto_add)

    def get_project(self, name):
        return self.db.get_project(name)

    def get_sample(self, name, project):
        return self.db.get_sample(name, project)

    def get_material(self, name):
        return self.db.get_material(name)

    def get_irradiation(self, name):
        return self.db.get_irradiation(name)

    def add_material(self, name):
        self.db.add_material(name)

    def add_sample(self, name, project, material):
        self.db.add_sample(name, project, material)

    def add_project(self, name):
        with self.db.session_ctx():
            self.db.add_project(name)

        p = os.path.join(paths.project_dir, name)
        os.mkdir(p)
        repo = Repo.init(p)

        # setup remotes

    def add_irradiation(self, name, doses=None):
        with self.db.session_ctx():
            self.db.add_irradiation(name)

        self.meta_repo.add_irradiation(name)
        self.meta_repo.add_chronology(name, doses)

    def add_irradiation_level(self, *args):
        with self.db.session_ctx():
            self.db.add_irradiation_level(*args)

    def update_chronology(self, name, doses):
        self.meta_repo.update_chronology(name, doses)

# ============= EOF =============================================



