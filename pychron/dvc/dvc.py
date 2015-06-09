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
import shutil
import time

from git import Repo
from traits.api import Instance, Str, Set, List
from apptools.preferences.preference_binding import bind_preference



# ============= standard library imports ========================
from itertools import groupby
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import remove_extension
from pychron.core.progress import progress_loader, progress_iterator
from pychron.dvc.defaults import TRIGA, HOLDER_24_SPOKES, LASER221, LASER65
from pychron.dvc.dvc_analysis import DVCAnalysis, experiment_path, analysis_path, PATH_MODIFIERS
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.git_archive.repo_manager import GitRepoManager, format_date
from pychron.github import Organization
from pychron.loggable import Loggable
from pychron.paths import paths

TESTSTR = {'blanks': 'auto update blanks', 'iso_evo': 'auto update iso_evo'}


class DVCException(BaseException):
    def __init__(self, attr):
        self._attr = attr

    def __repr__(self):
        return 'DVCException: neither DVCDatabase or MetaRepo have {}'.format(self._attr)

    def __str__(self):
        return self.__repr__()


def experiment_has_staged(ps):
    if not hasattr(ps, '__iter__'):
        ps = (ps,)

    changed = []
    repo = GitRepoManager()
    for p in ps:
        pp = os.path.join(paths.experiment_dataset_dir, p)
        repo.open_repo(pp)
        if repo.has_unpushed_commits():
            changed.append(p)

    return changed


def push_experiments(ps):
    repo = GitRepoManager()
    for p in ps:
        pp = os.path.join(paths.experiment_dataset_dir, p)
        repo.open_repo(pp)
        repo.push()


class DVC(Loggable):
    db = Instance('pychron.dvc.dvc_database.DVCDatabase')
    meta_repo = Instance('pychron.dvc.meta_repo.MetaRepo')

    meta_repo_name = Str
    organization = Str
    github_user = Str
    github_password = Str

    experiment_repo = Instance(GitRepoManager)
    auto_add = True
    pulled_experiments = Set
    selected_experiments = List

    def __init__(self, bind=True, *args, **kw):
        super(DVC, self).__init__(*args, **kw)

        if bind:
            self._bind_preferences()
            # self.synchronize()
            # self._defaults()

    def initialize(self):
        mrepo = self.meta_repo
        root = os.path.join(paths.dvc_dir, self.meta_repo_name)
        if os.path.isdir(os.path.join(root, '.git')):
            mrepo.open_repo(root)
        else:
            url = 'https://github.com/{}/{}.git'.format(self.organization, self.meta_repo_name)
            path = os.path.join(paths.dvc_dir, self.meta_repo_name)
            self.meta_repo.clone(url, path)

        # self.synchronize()
        if self.db.connect():
            self._defaults()
            return True

    # database

    # analysis processing
    def analysis_has_review(self, ai, attr):
        test_str = TESTSTR[attr]
        repo = self._get_experiment_repo(ai.experiment_id)
        for l in repo.get_log():
            if l.message.startswith(test_str):
                self.debug('{} {} reviewed'.format(ai, attr))
                return True
        else:
            self.debug('{} {} not reviewed'.format(ai, attr))

    def update_analyses(self, ans, msg):
        key = lambda x: x.experiment_id
        ans = sorted(ans, key=key)
        mod_experiments = []
        for expid, ais in groupby(ans, key=key):
            ais = map(lambda x: analysis_path(x.record_id, x.experiment_id, modifier='changeable'), ais)
            if self.experiment_add_analyses(expid, ais):
                self.experiment_commit(expid, msg)
                mod_experiments.append(expid)

        # ais = map(analysis_path, ais)
        #     if self.experiment_add_analyses(exp, ais):
        #         self.experiment_commit(exp, msg)
        #         mod_experiments.append(exp)
        return mod_experiments

    def experiment_add_analyses(self, experiment_id, paths):
        if not hasattr(paths, '__iter__'):
            paths = (paths,)

        repo = self._get_experiment_repo(experiment_id)

        changes = repo.get_local_changes()
        changed = False
        for p in paths:
            if os.path.basename(p) in changes:
                self.debug('Change Index adding: {}'.format(p))
                repo.add(p, commit=False, verbose=False)
                changed = True
        return changed

    def experiment_commit(self, project, msg):
        self.debug('Project commit: {} msg: {}'.format(project, msg))
        repo = self._get_experiment_repo(project)
        repo.commit(msg)

    def save_icfactors(self, ai, dets, fits, refs):
        self.info('Saving icfactors for {}'.format(ai))
        ai.dump_icfactors(dets, fits, refs)

    def save_blanks(self, ai, keys, refs):
        self.info('Saving blanks for {}'.format(ai))
        ai.dump_blanks(keys, refs)

    def save_fits(self, ai, keys):
        self.info('Saving fits for {}'.format(ai))
        ai.dump_fits(keys)

    def find_references(self, times, atypes):
        records = self.db.find_references(times, atypes)
        return self.make_analyses(records)

    def make_analyses(self, records, calculate_F=False):
        # load repositories
        # {r.experiment_id for r in records}
        exps = {r.experiment_id for r in records}
        if self.pulled_experiments:
            exps = exps - self.pulled_experiments

            self.pulled_experiments.union(exps)
        else:
            self.pulled_experiments = exps

        if exps:
            progress_iterator(exps, self._load_repository, threshold=1)

        st = time.time()
        wrapper = lambda *args: self._make_record(calculate_F=calculate_F, *args)

        ret = progress_loader(records, wrapper, threshold=1)
        et = time.time()-st
        n = len(records)

        self.debug('Make analysis time, total: {}, n: {}, average: {}'.format(et, n, et/float(n)))
        return ret

    def synchronize(self, pull=True):
        """
        pull meta_repo changes

        :return:
        """
        if pull:
            self.meta_repo.pull()
        else:
            self.meta_repo.push()

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

    def add_experiment(self, identifier):
        org = Organization(self.organization, usr=self.github_user, pwd=self.github_password)
        if identifier in org.repos:
            self.warning_dialog('Experiment "{}" already exists'.format(identifier))
        else:
            root = os.path.join(paths.experiment_dataset_dir, identifier)

            if os.path.isdir(root):
                self.warning_dialog('{} already exists.'.format(root))
            else:
                self.info('Creating repository. {}'.format(identifier))
                org.create_repo(identifier, auto_init=True)

                url = '{}/{}/{}.git'.format(paths.git_base_origin, self.organization, identifier)
                Repo.clone_from(url, root)

    def add_irradiation(self, name, doses=None):
        with self.db.session_ctx():
            if self.db.get_irradiation(name):
                self.warning('irradiation {} already exists'.format(name))
                return

            self.db.add_irradiation(name)

        self.meta_repo.add_irradiation(name)
        self.meta_repo.add_chronology(name, doses)
        self.meta_repo.commit('added irradiation {}'.format(name))
        self.meta_repo.push()

        self.add_experiment(name)

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
        changes = self.meta_repo.has_staged()
        if changes:
            self.debug('meta repo has changes: {}'.format(changes))
            self.meta_repo.report_status()
            self.meta_repo.commit(msg)
        else:
            self.debug('no changes to meta repo')

    def get_meta_head(self):
        return self.meta_repo.get_head()

    def sync_repo(self, name):
        """
        1. open the repo or create and empty one
        2. create the origin remote
        3. pull changes from origin

        """
        url = 'https://github.com/{}/{}.git'.format(self.organization, name)
        repo = self._get_experiment_repo(name)
        root = os.path.join(paths.experiment_dataset_dir, name)
        if os.path.isdir(os.path.join(root, '.git')):
            repo.pull()
        else:
            repo.clone(url, root)

        return True

    def add_experiment_association(self, expid, runspec):
        db = self.db
        with db.session_ctx():
            dban = db.get_analysis_uuid(runspec.uuid)
            for e in dban.experiment_associations:
                if e.experimentName == expid:
                    break
            else:
                db.add_experiment_association(expid, dban)

            src_expid = runspec.experiment_id
            if src_expid != expid:
                repo = self._get_experiment_repo(expid)

                for m in PATH_MODIFIERS:
                    src = analysis_path(runspec.record_id, src_expid, modifier=m)
                    dest = analysis_path(runspec.record_id, expid, modifier=m, mode='w')

                    shutil.copyfile(src, dest)
                    repo.add(dest, commit=False)
                repo.commit('added experiment association')

    def rollback_experiment_repo(self, expid):
        repo = self._get_experiment_repo(expid)

        cpaths = repo.get_local_changes()
        # cover changed paths to a list of analyses

        # select paths to revert
        rpaths = ('.',)
        repo.cmd('checkout', '--', ' '.join(rpaths))
        for p in rpaths:
            self.debug('revert changes for {}'.format(p))

        head = repo.get_head(hexsha=False)
        msg = 'Changes to {} reverted to Commit: {}\n' \
              'Date: {}\n' \
              'Message: {}'.format(expid, head.hexsha[:10],
                                   format_date(head.committed_date),
                                   head.message)
        self.information_dialog(msg)

    # private
    def __getattr__(self, item):
        try:
            return getattr(self.db, item)
        except AttributeError:
            try:
                return getattr(self.meta_repo, item)
            except AttributeError, e:
                # print e, item
                raise DVCException(item)

    def _load_repository(self, expid, prog, i, n):
        if prog:
            prog.change_message('Loading repository {}. {}/{}'.format(expid, i, n))
            # repo = GitRepoManager()
            # repo.open_repo(expid, root=paths.experiment_dataset_dir)

        self.sync_repo(expid)

    def _make_record(self, record, prog, i, n, calculate_F=False):
        if prog:
            prog.change_message('Loading analysis {}. {}/{}'.format(record.record_id, i, n))

        expid = record.experiment_id
        if not expid:
            exps = record.experiment_ids
            self.debug('Analysis {} is associated multiple experiments '
                       '{}'.format(record.record_id, ','.join(exps)))
            expid = None
            if self.selected_experiments:
                rr = []
                for si in self.selected_experiments:
                    if si in exps:
                        rr.append(si)
                if rr:
                    if len(rr) > 1:
                        expid = self._get_requested_experiment_id(rr)
                    else:
                        expid = rr[0]

            if expid is None:
                expid = self._get_requested_experiment_id(exps)

        a = DVCAnalysis(record.record_id, expid)

        # load irradiation
        chronology = self.meta_repo.get_chronology(a.irradiation)
        a.set_chronology(chronology)

        pname = self.db.get_production_name(a.irradiation, a.irradiation_level)

        prod = self.meta_repo.get_production(pname)
        a.set_production(pname, prod)

        if calculate_F:
            a.calculate_F()

        return a

    def _get_experiment_repo(self, experiment_id):
        repo = self.experiment_repo
        path = experiment_path(experiment_id)

        if repo is None or repo.path != path:
            self.debug('make new repomanager for {}'.format(path))
            repo = GitRepoManager()
            repo.path = path
            repo.open_repo(path)
            self.experiment_repo = repo

        return repo

    def _bind_preferences(self):

        prefid = 'pychron.dvc'
        for attr in ('meta_repo_name', 'organization', 'github_user', 'github_password'):
            bind_preference(self, attr, '{}.{}'.format(prefid, attr))

        prefid = 'pychron.dvc.db'
        for attr in ('username', 'password', 'name', 'host'):
            bind_preference(self.db, attr, '{}.{}'.format(prefid, attr))

    def _defaults(self):
        # self.db.create_all(Base.metadata)
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
        return DVCDatabase(kind='mysql',
                           username='root',
                           password='Argon',
                           host='localhost',
                           name='pychronmeta')

    def _meta_repo_default(self):
        return MetaRepo()

# ============= EOF =============================================
