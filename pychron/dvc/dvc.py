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
from itertools import groupby
import subprocess

from traits.api import Instance, Str
from apptools.preferences.preference_binding import bind_preference


# ============= standard library imports ========================
import os
from git import Repo
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import remove_extension
from pychron.dvc.defaults import TRIGA, HOLDER_24_SPOKES, LASER221, LASER65
from pychron.dvc.dvc_analysis import DVCAnalysis, project_path, analysis_path
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.git_archive.repo_manager import GitRepoManager
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

    project_repo = Instance(GitRepoManager)

    def __init__(self, *args, **kw):
        super(DVC, self).__init__(*args, **kw)
        self._bind_preferences()

        # self.synchronize()
        # self._defaults()

    def initialize(self):
        self.synchronize()
        self._defaults()

    def fetch_meta(self):
        self.meta_repo.fetch()

    # database
    def load_db(self):

        if self.meta_repo.out_of_date():
            self.info('rebuilding local database from origin')
            self.info('pulling changes')
            self.meta_repo.pull()

            path = paths.meta_db
            if os.path.isfile(path):
                self.info('removing current db')
                os.remove(path)

            txtdb_path = paths.meta_txtdb
            self.info('loading db into sqlite')
            ret = subprocess.check_call(['sqlite3', path, '.read {}'.format(txtdb_path)])
            if ret:
                self.warning_dialog('There was a problem loading the database')
                return

        self.db.connect(force=True)

    def dump_db(self, msg=None):
        if msg is None:
            msg = 'Updated meta database'

        path = paths.meta_db
        txtdb = paths.meta_txtdb

        with open(txtdb, 'w') as wfile:
            subprocess.check_call(['sqlite3', path, '.dump'], stdout=wfile)

        self.meta_repo.add(txtdb, commit=False)
        self.meta_repo.commit(msg)
        self.meta_repo.push()

    # analysis processing

    def _get_project_repo(self, project):
        repo = self.project_repo
        path = project_path(project)

        if repo is None or repo.path != path:
            self.debug('make new repo for {}'.format(path))
            repo = GitRepoManager()
            repo.path = path
            repo.open_repo(path)
            self.project_repo = repo

        return repo

    def update_analyses(self, ans, msg):
        key = lambda x: x.project
        ans = sorted(ans, key=key)
        for project, ais in groupby(ans, key=key):
            ais = map(analysis_path, ais)
            if self.project_add(project, ais):
                self.project_commit(project, msg)

    def project_add(self, project, paths):
        if not hasattr(paths, '__iter__'):
            paths = (paths,)

        repo = self._get_project_repo(project)

        changes = repo.get_local_changes()
        changed = False
        for p in paths:
            if os.path.basename(p) in changes:
                repo.add(p, commit=False)
                changed = True
        return changed

    def project_commit(self, project, msg):
        repo = self._get_project_repo(project)
        repo.commit(msg)

    def save_blanks(self, ai, keys, refs):
        self.info('Saving blanks for {}'.format(ai))
        ai.dump_blanks(keys, refs)

    def save_fits(self, ai, keys):
        self.info('Saving fits')
        ai.dump_fits(keys)

    def find_references(self, times, atypes):
        print 'times', times
        records = self.db.find_references(times, atypes)
        return self.make_analyses(records)

    def make_analyses(self, records):
        records = map(self._make_record, records)
        return records

    def synchronize(self, pull=True):
        """
        pull meta_repo changes

        rsync the database
        :return:
        """
        if pull:
            self.meta_repo.pull()
            self.load_db()

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

    def _make_record(self, record):
        a = DVCAnalysis(record)

        # load irradiation
        chronology = self.meta_repo.get_chronology(a.irradiation)
        a.set_chronology(chronology)

        pname = self.db.get_production_name(a.irradiation, a.irradiation_level)
        # production = self.meta_repo.get_production(a.irradiation, a.irradiation_level)
        prod = self.meta_repo.get_production(pname)
        a.set_production(pname, prod)

        return a

    # adders db
    # def add_analysis(self, **kw):
    #     with self.db.session_ctx():
    #         self.db.add_material(**kw)

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
    # def update_chronology(self, name, doses):
    # self.meta_repo.update_chronology(name, doses)
    #
    # def update_scripts(self, name, path):
    # self.meta_repo.update_scripts(name, path)
    #
    # def update_experiment_queue(self, name, path):
    #     self.meta_repo.update_experiment_queue(name, path)

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
        return MetaRepo()

# ============= EOF =============================================
