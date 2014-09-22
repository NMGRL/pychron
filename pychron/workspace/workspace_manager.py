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
import time

from traits.api import Property, \
    Event, List, Str, HasTraits, Any, cached_property

# ============= standard library imports ========================
import shutil
from git import GitCommandError
import os
# ============= local library imports  ==========================
import yaml
from pychron.core.helpers.filetools import list_directory2, fileiter
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.workspace.tasks.views import DiffView


class Commit(HasTraits):
    message = Str
    date = Str
    hexsha = Str
    summary = Property
    def _get_summary(self):
        return '{} {}'.format(self.date, self.message)


class Manifest(object):
    def __init__(self, p):
        p = self.filename(p)
        if not os.path.isfile(p):
            with open(p, 'w'):
                pass
        self.path = p

    @classmethod
    def exists(cls, p):
        return os.path.isfile(cls.filename(p))

    @classmethod
    def filename(cls, p):
        return os.path.join(p, 'MANIFEST')

    def add(self, name):
        with open(self.path, 'r') as fp:
            exists = next((line for line in fileiter(fp, strip=True)
                           if line == name), None)

        if not exists:
            with open(self.path, 'a') as fp:
                fp.write('{}\n'.format(name))

    def remove(self, name):
        with open(self.path, 'w') as fp:
            for line in fileiter(self.path, strip=True):
                if line == name:
                    continue
                else:
                    fp.write('{}\n'.format(line))

    @property
    def names(self):
        with open(self.path, 'r') as fp:
            return list(fileiter(fp, strip=True))


class WorkspaceManager(GitRepoManager):
    # index_db = Instance(IndexAdapter)
    # test = Button
    selected = Any
    dclicked = Event
    repo_updated = Event

    branches = List
    commits = List
    selected_path_commits = List
    selected_text = Str
    selected_commits = List

    def diff_selected(self):
        if self.selected.endswith('.yaml'):
            if len(self.selected_commits) == 2:
                l, r = self.selected_commits
                dd = self._calculate_diff_dict(l, r)
                dv = DiffView(l.summary, r.summary, dd)
                self.application.open_view(dv)

    def _calculate_diff_dict(self, left, right):
        left = self.get_commit(left.hexsha)
        right =self.get_commit(right.hexsha)

        ds = left.diff(right, create_patch=True)

        attrs = ['age','age_err',
                 'age_err_wo_j', 'age_err_wo_j_irrad',
                 'ar39decayfactor',
                 'ar37decayfactor',
                 'j','j_err',
                 'tag',
                 'material','sample',
                 ('constants', 'abundance_sensitivity','atm4036','lambda_k'),
                 ('production_ratios','Ca_K','Cl_K')
                 ]

        if not isinstance(attrs, (tuple, list)):
            attrs = (attrs, )

        attr_diff = []
        for ci in ds.iter_change_type('M'):
            try:
                a = ci.a_blob.data_stream
            except Exception,e:
                print 'a',e
                continue

            try:
                b = ci.b_blob.data_stream
            except Exception, e:
                print 'b',e
                continue

            ayd = yaml.load(a)
            byd = yaml.load(b)

            #use the first analysis only
            ayd = ayd[ayd.keys()[0]]
            byd = byd[byd.keys()[0]]

            def func(ad,bd,attr):
                try:
                    av = ad[attr]
                except KeyError:
                    av = None

                try:
                    bv = bd[attr]
                except KeyError:
                    bv = None

                attr_diff.append((attr, av, bv))

            for attr in attrs:
                if isinstance(attr, (list, tuple)):
                    subdict=attr[0]
                    sa,sb=ayd[subdict], byd[subdict]
                    for ai in attr[1:]:
                        func(sa, sb, ai)
                else:
                    func(ayd, byd, attr)

            aisos = ayd['isotopes']
            bisos = byd['isotopes']
            for aisod in aisos:
                name=aisod['name']
                av = aisod['value']

                bisod = next((b for b in bisos if b['name']==name), None)
                bv= bisod['value'] if bisod else 0

                attr_diff.append((name, av, bv))

        return attr_diff

    def open_repo(self, name, root=None):
        super(WorkspaceManager, self).open_repo(name, root)

        e = Manifest.exists(self.path)
        # init manifest object
        self._manifest = Manifest(self.path)
        if not e:
            self.add(self._manifest.path, msg='Added manifest file')

        self.create_branch('develop')
        self.checkout_branch('develop')

    def load_branches(self):
        self.branches = [bi.name for bi in self._repo.branches]

    def create_branch(self, name):
        super(WorkspaceManager, self).create_branch(name)
        self.load_branches()

    def find_existing(self, names):
        return [os.path.splitext(ni)[0] for ni in self._manifest.names if ni in names]

    def add_to_manifest(self, path):
        self._manifest.add(os.path.basename(path))

    def add_manifest_to_index(self):
        p = self._manifest.path
        index = self.index
        index.add([p])

    def commit_manifest(self):
        p = self._manifest.path
        self._add_to_repo(p, msg='Updated manifest')

    def add_analysis(self, path, commit=True, message=None, **kw):
        """
            path: absolute path to flat file
            commit: commit changes
            message: message to use for commit


            1. copy file at path to the repository
            2. add record to index

        """

        repo = self._repo
        # copy file to repo
        dest = os.path.join(repo.working_dir, os.path.basename(path))
        if not os.path.isfile(dest):
            shutil.copyfile(path, dest)

        # add to master changeset
        index = repo.index
        index.add([dest])
        if commit:
            if message is None:
                message = 'added record {}'.format(path)
            index.commit(message)

        self.repo_updated = True
        #add to sqlite index
        # im = self.index_db
        # im.add(repo=repo.working_dir, **kw)

    def modify_analysis(self, path, message=None, branch='develop'):
        """
        commit the modification to path to the working branch
        """
        self.checkout_branch(branch)
        index = self.index
        index.add([path])
        if message is None:
            message = 'modified record {}'.format(os.path.relpath(path, self.path))
        index.commit(message)

    def _load_branch_history(self):
        repo = self._repo
        hexshas = self._get_branch_history()
        # [repo.rev_parse(c) for c in hexshas]
        # self.commits = [self.commit_factory(ci) for ci in hexshas]
        self.commits = self._parse_commits(hexshas)

    def _parse_commits(self, hexshas):
        def factory(ci):
            repo = self._repo
            obj = repo.rev_parse(ci)
            cx = Commit(message=obj.message,
                        hexsha=obj.hexsha,
                        date=time.strftime("%m/%d/%Y %H:%M", time.gmtime(obj.committed_date)))
            return cx

        return [factory(ci) for ci in hexshas]

    def _load_file_history(self, p):
        repo = self._repo
        try:
            hexshas = repo.git.log('--pretty=%H', '--follow', '--', p).split('\n')
            # cs = [repo.rev_parse(c).message for c in hexshas]
            # self.selected_path_commits = cs
            self.selected_path_commits = self._parse_commits(hexshas)
        except GitCommandError:
            self.selected_path_commits = []

    def _load_file_text(self, new):
        with open(new, 'r') as fp:
            self.selected_text = fp.read()

    def _selected_fired(self, new):
        if new:
            self._load_file_text(new)
            self._load_file_history(new)

    def _dclicked_fired(self, new):
        if new:
            self._load_file_history(new)

    def _selected_branch_changed(self, new):
        if new:
            self.checkout_branch(new)


class ArArWorkspaceManager(WorkspaceManager):
    nanalyses = Property(depends_on='path, repo_updated')

    @cached_property
    def _get_nanalyses(self):
        return len(list_directory2(self.path, extension='.yaml'))

        # ============= EOF =============================================
        # def schema_diff(self, attrs):
        # """
        #         show the diff for the given schema keyword `attr` between the working and master
        #     """
        #     repo = self._repo
        #     master_commit = repo.heads.master.commit
        #     working_commit = repo.heads.working.commit
        #
        #     ds = working_commit.diff(master_commit, create_patch=True)
        #     # ds = working_commit.diff(master_commit)
        #
        #     if not isinstance(attrs, (tuple, list)):
        #         attrs = (attrs, )
        #
        #     attr_diff = {}
        #     for ci in ds.iter_change_type('M'):
        #         a = ci.a_blob.data_stream
        #
        #         ayd = yaml.load(a)
        #         # print 'a', a.read()
        #         b = ci.b_blob.data_stream
        #
        #         byd = yaml.load(b)
        #         for attr in attrs:
        #
        #             try:
        #                 av = ayd[attr]
        #             except KeyError:
        #                 av = None
        #
        #             try:
        #                 bv = byd[attr]
        #             except KeyError:
        #                 bv = None
        #
        #             attr_diff[attr] = av == bv, av, bv
        #
        #     return attr_diff