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
import os

from pychron.dvc import dvc_load, dvc_dump


def fix_repo(d):
    for p in os.listdir(d):
        print('asdf', p)
        if p =='.git':
            continue

        dd = os.path.join(d, p)

        if os.path.isdir(dd):
            for ap in os.listdir(dd):
                ap = os.path.join(dd, ap)
                if os.path.isfile(ap):
                    fix_repo_identifier(ap, 'Irradiation-NM-284')


def fix_repo_identifier(p, nid):
    obj = dvc_load(p)
    if obj['repository_identifier'] !=nid:
        obj['repository_identifier'] = nid
        dvc_dump(obj, p)


if __name__ == '__main__':
    d = '/Users/ross/PychronDev/data/.dvc/repositories/Irradiation-NM-284'
    fix_repo(d)

# ============= EOF =============================================
