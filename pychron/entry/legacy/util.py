# ===============================================================================
# Copyright 2020 ross
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

from pychron.dvc.dvc import DVC


class CSVHeader:
    def __init__(self, h):
        self._h = h

    def get(self, row, key, cast=None):
        if cast is None:
            cast = str

        idx = self.idx(key)
        return cast(row[idx].strip())

    def idx(self, key):
        try:
            return self._h.index(key)
        except ValueError as e:
            print(e, self._h)


class XLSHeader(CSVHeader):

    def get(self, row, key, cast=None):
        if cast is None:
            cast = str
        idx = self._h.index(key)
        return cast(row[idx].value)


def get_dvc():
    from pychron.paths import paths
    paths.build('~/PychronDev')
    meta_name = 'NMGRLMetaDataLegacy'
    dvc = DVC(bind=False,
              organization='NMGRLDataDev',
              meta_repo_name=meta_name)

    paths.meta_root = os.path.join(paths.dvc_dir, dvc.meta_repo_name)
    dvc.db.trait_set(host='localhost',
                     username='root',  # os.environ.get('ARGONSERVER_DB_USER'),
                     password='geochr0n!!',
                     name='pychrondvc_import',
                     kind='mysql')
    if not dvc.initialize():
        print('failed to initalize')
        return
    return dvc

# ============= EOF =============================================
