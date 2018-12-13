# ===============================================================================
# Copyright 2018 ross
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
from pychron.dvc import analysis_path, dvc_load, dvc_dump


def get_runlist():
    return ['66573-01A', '66573-01B', '66573-01C', '66573-01D', '66573-01E', '66573-01F',
            '66573-01G', '66573-01H', '66573-01I', '66573-01J', '66573-01K', '66573-01L', '66573-01M',
            '66572-01A', '66572-01B', '66572-01C', '66572-01D', '66572-01E', '66572-01F',
            '66572-01G', '66572-01H', '66572-01I', '66572-01J', '66572-01K', '66572-01L',
            '66572-01M']


def fix():
    repository = 'Saifuddeen01097'
    root = '/Users/ross/PychronDev/data/.dvc/repositories'
    runlist = get_runlist()
    for runid in runlist:
        for modifier in ('intercepts',):
            fix_run(runid, repository, root, modifier)
        fix_iso_list(runid, repository, root)


def fix_iso_list(runid, repository, root):
    path = analysis_path(runid, repository, root=root)
    # print('asdf', path)
    obj = dvc_load(path)
    isotopes = obj['isotopes']
    try:
        v = isotopes.pop('PHHCbs')
        v['name'] = 'Ar39'
        isotopes['Ar39'] = v
        obj['isotopes'] = isotopes
        dvc_dump(obj, path)
    except KeyError:
        return


def fix_run(runid, repository, root, modifier):
    path = analysis_path(runid, repository, root=root, modifier=modifier)
    # print('asdf', path)
    obj = dvc_load(path)
    # print('ff', obj)
    try:
        v = obj.pop('PHHCbs')
        obj['Ar39'] = v
        dvc_dump(obj, path)
        msg = 'fixed'
    except KeyError:
        msg = 'skipped'

    print(runid, msg)


if __name__ == '__main__':
    fix()
# ============= EOF =============================================
