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
# ============= standard library imports ========================
import json
import os
from pprint import pformat

from pychron.core.helpers.filetools import subdirize, add_extension
from pychron.paths import paths

__version__ = '0.1'


class AnalysisNotAnvailableError(BaseException):
    def __init__(self, root, runid):
        self._root = root
        self._runid = runid

    def __str__(self):
        return 'Analysis Not Available. {} - {}'.format(self._root, self._runid)


def dvc_dump(obj, path):
    with open(path, 'w') as wfile:
        try:
            json.dump(obj, wfile, indent=4, sort_keys=True)
        except TypeError, e:
            print 'dvc dump exception. error:{}, {}'.format(e, pformat(obj))


def dvc_load(path):
    if os.path.isfile(path):
        with open(path, 'r') as rfile:
            return json.load(rfile)
    else:
        return {}


MASSES = None


def get_masses():
    from pychron.paths import paths

    global MASSES
    if MASSES is None:
        path = os.path.join(paths.meta_root, 'molecular_weights.json')
        MASSES = dvc_load(path)

    return MASSES


SPEC_SHAS = {}


def get_spec_sha(p):
    if p not in SPEC_SHAS:
        sd = dvc_load(p)
        SPEC_SHAS[p] = sd

    return SPEC_SHAS[p]


def analysis_path(runid, repository, modifier=None, extension='.json', mode='r'):
    root = os.path.join(paths.repository_dataset_dir, repository)

    l = 3
    if runid.count('-') > 1:
        args = runid.split('-')[:-1]
        if len(args[0]) == 1:
            l = 4
        else:
            l = 5

    try:
        root, tail = subdirize(root, runid, l=l, mode=mode)
    except TypeError:
        raise AnalysisNotAnvailableError(root, runid)

    if modifier:
        d = os.path.join(root, modifier)
        if not os.path.isdir(d):
            if mode == 'r':
                return

            os.mkdir(d)

        root = d
        fmt = '{}.{}'
        if modifier.startswith('.'):
            fmt = '{}{}'
        tail = fmt.format(tail, modifier[:4])

    name = add_extension(tail, extension)

    return os.path.join(root, name)


def repository_path(project):
    return os.path.join(paths.dvc_dir, 'repositories', project)


def make_ref_list(refs):
    return [{'record_id': r.record_id, 'uuid': r.uuid, 'exclude': r.temp_status} for r in refs]

# ============= EOF =============================================
