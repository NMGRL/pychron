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
from traits.api import Instance, Str
from apptools.preferences.preference_binding import bind_preference
# ============= standard library imports ========================
import os
from git import Repo
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import remove_extension
from pychron.dvc.defaults import TRIGA, HOLDER_24_SPOKES, LASER221, LASER65
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.github import Organization
from pychron.loggable import Loggable
from pychron.paths import paths


class DVCException(BaseException):
    def __init__(self, attr):
        self._attr = attr

    def __repr__(self):
        return 'DVCException: neither DVCDatbase or MetaRepo have {}'.format(self._attr)

    def __str__(self):
        return self.__repr__()


class DVC(Loggable):
    db = Instance('pychron.dvc.dvc_database.DVCDatabase')
    meta_repo = Instance('pychron.dvc.meta_repo.MetaRepo')
    clear_db = False
    auto_add = False

    repo_root = Str
    repo_user = Str
    repo_password = Str

    def __init__(self, *args, **kw):
        super(DVC, self).__init__(*args, **kw)
        self._bind_preferences()

        self.synchronize()

        self.db.connect()
        self._defaults()

    def make_analyses(self, records):
        print records
        return records

    def synchronize(self, pull=True):
        """
        pull meta_repo changes

        rsync the database
        :return:
        """
        if pull:
            self.meta_repo.pull()
            self.db.connect(force=True)
        else:
            self.meta_repo.push()

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
        # self.meta_repo.add(path, commit=False)
        #
        # self.meta_repo.commit(msg)

    def session_ctx(self):
        return self.db.session_ctx()

    def __getattr__(self, item):
        try:
            return getattr(self.db, item)
        except AttributeError:
            try:
                return getattr(self.meta_repo, item)
            except AttributeError, e:
                # print e, item
                raise DVCException(item)

    # def get_mass_spectrometers(self):
    # return self.db.get_mass_spectrometers()
    #
    # def get_projects(self, **kw):
    # return self.db.get_projects(**kw)
    #
    # def get_project(self, name):
    #     return self.db.get_project(name)
    #
    # def get_sample(self, name, project):
    #     return self.db.get_sample(name, project)
    #
    # def get_material(self, name):
    #     return self.db.get_material(name)
    #
    # def get_irradiation(self, name):
    #     return self.db.get_irradiation(name)
    #
    # def get_load_holder_holes(self, name):
    #     return self.meta_repo.get_load_holder_holes(name)

    # adders db
    def add_analysis(self, **kw):
        with self.db.session_ctx():
            self.db.add_material(**kw)

    def add_measured_position(self, *args, **kw):
        with self.db.session_ctx():
            self.db.add_measured_position(*args, **kw)

    def add_material(self, name):
        with self.db.session_ctx():
            self.db.add_material(name)

    def add_sample(self, name, project, material):
        with self.db.session_ctx():
            self.db.add_sample(name, project, material)

    def add_irradiation_level(self, *args):
        with self.db.session_ctx():
            self.db.add_irradiation_level(*args)

    # adders db and repo
    def add_project(self, name):
        org = Organization(self.repo_root, usr=self.repo_user, pwd=self.repo_password)

        # check if project is available
        if name in org.repos:
            self.warning_dialog('Project "{}" already exists'.format(name))
            return

        with self.db.session_ctx():
            self.db.add_project(name)

        p = os.path.join(paths.project_dir, name)
        os.mkdir(p)
        repo = Repo.init(p)

        # add project to github
        # org.create_repo(name, auto_init=True)

        # setup remotes
        # url = 'https://github.com/{}/'.format(self.repo_root, name)
        # repo.create_remote('origin', url)

        return True

    def add_irradiation(self, name, doses=None):
        with self.db.session_ctx():
            self.db.add_irradiation(name)

        self.meta_repo.add_irradiation(name)
        self.meta_repo.add_chronology(name, doses)

    def add_load_holder(self, name, path_or_txt):
        with self.db.session_ctx():
            self.db.add_load_holder(name)
        self.meta_repo.add_load_holder(name, path_or_txt)

    # updaters
    def update_chronology(self, name, doses):
        self.meta_repo.update_chronology(name, doses)

    def update_scripts(self, name, path):
        self.meta_repo.update_scripts(name, path)

    def update_scripts(self, name, path):
        self.meta_repo.update_experiment_queue(name, path)

    def meta_commit(self, msg):
        if self.meta_repo.has_staged():
            self.debug('meta repo has changes')
            self.meta_repo.report_status()
            self.meta_repo.commit(msg)

    def get_meta_head(self):
        return self.meta_repo.get_head()

    # private
    def _bind_preferences(self):
        prefid = 'pychron.dvc'
        for attr in ('repo_root', 'repo_user', 'repo_password'):
            bind_preference(self, attr, '{}.{}'.format(prefid, attr))

    def _defaults(self):
        with self.db.session_ctx():
            for tag, func in (('irradiation holders', self._add_default_irradiation_holders),
                              ('productions', self._add_default_irradiation_productions),
                              ('load holders', self._add_default_load_holders)):
                d = os.path.join(self.meta_repo.path, tag.replace(' ', '_'))
                if not os.path.isdir(d):
                    os.mkdir(d)
                    if self.auto_add:
                        func()
                    elif self.confirmation_dialog('You have no {}. Would you like to add some defaults?'.format(tag)):
                        func()

    def _add_default_irradiation_productions(self):
        ds = (('TRIGA.txt', TRIGA),)
        self._add_defaults(ds, 'productions')

    def _add_default_irradiation_holders(self):
        ds = (('24Spokes.txt', HOLDER_24_SPOKES),)
        self._add_defaults(ds, 'irradiation_holders', )

    def _add_default_load_holders(self):
        ds = (('221.txt', LASER221),
              ('65.txt', LASER65))
        self._add_defaults(ds, 'load_holders', self.db.add_load_holder)

    def _add_defaults(self, defaults, root, dbfunc=None):
        commit = False
        repo = self.meta_repo
        for name, txt in defaults:
            p = os.path.join(repo.path, root, name)
            if not os.path.isfile(p):
                with open(p, 'w') as wfile:
                    wfile.write(txt)
                repo.add(p, commit=False)
                commit = True
                if dbfunc:
                    name = remove_extension(name)
                    dbfunc(name)

        if commit:
            repo.commit('added default {}'.format(root.replace('_', ' ')))

    def _db_default(self):
        return DVCDatabase(clear=self.clear_db, auto_add=self.auto_add)

    def _meta_repo_default(self):
        return MetaRepo(auto_add=self.auto_add)

# ============= EOF =============================================



