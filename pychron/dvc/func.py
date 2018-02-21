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

# ============= standard library imports ========================
from __future__ import absolute_import
import glob
import os
from datetime import datetime
from git import Repo
from traits.api import Str, Bool, HasTraits

from pychron import json
from pychron.dvc import analysis_path
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths


def repository_has_staged(ps, remote='origin', branch='master'):
    if not hasattr(ps, '__iter__'):
        ps = (ps,)

    changed = []
    # repo = GitRepoManager()
    for p in ps:
        pp = os.path.join(paths.repository_dataset_dir, p)
        repo = Repo(pp)

        if repo.git.log('{}/{}..HEAD'.format(remote, branch), '--oneline'):
            changed.append(p)

    return changed


def push_repositories(ps, remote='origin', branch='master', quiet=True):
    for p in ps:
        pp = os.path.join(paths.repository_dataset_dir, p)
        # repo = Repo(pp)
        repo = GitRepoManager()
        repo.open_repo(pp)

        if repo.smart_pull(remote=remote, branch=branch, quiet=quiet):
            repo.push(remote=remote, branch=branch)


def reviewed(items):
    return any((i for i in items if i.status))


def is_blank_reviewed(obj, date):
    return make_rsd_items(obj, date, 'Bk')


def is_icfactors_reviewed(obj, date):
    return make_rsd_items(obj, date, 'IC')


def is_intercepts_reviewed(obj, date):
    return make_rsd_items(obj, date, 'Iso Evo')


def make_rsd_items(obj, date, tag):
    items = [RSDItem(process='{} {}'.format(k, tag), date=date, status=iso.get('reviewed', False)) for k,iso in
             obj.items()]
    return items


class RSDItem(HasTraits):
    process = Str
    status = Bool
    date = Str


def get_review_status(record):
    ms = 0
    ritems = []
    root = os.path.join(paths.repository_dataset_dir, record.repository_identifier)
    if os.path.isdir(root):
        repo = Repo(root)
        for m, func in (('blanks', is_blank_reviewed),
                        ('intercepts', is_intercepts_reviewed),
                        ('icfactors', is_icfactors_reviewed)):
            p = analysis_path(record.record_id, record.repository_identifier, modifier=m)
            if os.path.isfile(p):
                with open(p, 'r') as rfile:
                    obj = json.load(rfile)
                    date = repo.git.log('-1', '--format=%cd', p)
                    items = func(obj, date)
                    if items:
                        if reviewed(items):
                            ms += 1
                        ritems.extend(items)

        # setattr(record, '{}_review_status'.format(m), (reviewed, date))
    record.review_items = ritems
    ret = 'Intermediate'  # intermediate
    if not ms:
        ret = 'Default'  # default
    elif ms == 3:
        ret = 'All'  # all

    record.review_status = ret


def find_interpreted_age_path(idn, repositories, prefixlen=3):
    prefix = idn[:prefixlen]
    suffix = '{}*.ia.json'.format(idn[prefixlen:])
    # ret = []
    # for e in repositories:
    #     pathname = os.path.join(paths.repository_dataset_dir,
    #                             e, prefix, 'ia', suffix)
    #     ps = glob.glob(pathname)
    #     if ps:
    #         ret.extend(ps)

    ret = [p for repo in repositories
           for p in glob.glob(os.path.join(paths.repository_dataset_dir, repo, prefix, 'ia', suffix))]
    return ret


class GitSessionCTX(object):
    def __init__(self, parent, repository_identifier, message):
        self._parent = parent
        self._repository_id = repository_identifier
        self._message = message
        self._parent.get_repository(repository_identifier)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._parent.is_dirty():
                self._parent.repository_commit(self._repository_id, self._message)

# ============= EOF =============================================
