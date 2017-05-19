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

# ============= standard library imports ========================
import glob
import json
import os
from datetime import datetime

from git import Repo

from pychron.dvc import analysis_path
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
        repo = Repo(pp)

        if repo.smart_pull(remote=remote, branch=branch, quiet=quiet):
            repo.git.push(remote, branch)


def get_review_status(record):
    ms = 0
    for m in ('blanks', 'intercepts', 'icfactors'):
        p = analysis_path(record.record_id, record.repository_identifier, modifier=m)
        date = ''
        with open(p, 'r') as rfile:
            obj = json.load(rfile)
            reviewed = obj.get('reviewed', False)
            if reviewed:
                dt = datetime.fromtimestamp(os.path.getmtime(p))
                date = dt.strftime('%m/%d/%Y')
                ms += 1

        setattr(record, '{}_review_status'.format(m), (reviewed, date))

    ret = 'Intermediate'  # intermediate
    if not ms:
        ret = 'Default'  # default
    elif ms == 3:
        ret = 'All'  # all

    record.review_status = ret


def find_interpreted_age_path(idn, repositories, prefixlen=3):
    prefix = idn[:prefixlen]
    # suffix = '{}.ia.json'.format(idn[prefixlen:])
    suffix = '*.ia.json'

    for e in repositories:
        pathname = '{}/{}/{}/ia/{}'.format(paths.repository_dataset_dir, e, prefix, suffix)
        ps = glob.glob(pathname)
        if ps:
            return ps


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
