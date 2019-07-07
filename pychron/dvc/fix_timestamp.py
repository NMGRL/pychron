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

from pyface.message_dialog import warning

from pychron.dvc import analysis_path
from pychron.dvc.dvc import DVC
from pychron.paths import paths


def get_dvc():
    conn = dict(host=os.environ.get('ARGONSERVER_HOST'),
                username='jross',  # os.environ.get('ARGONSERVER_DB_USER'),
                password=os.environ.get('ARGONSERVER_DB_PWD'),
                name='pychrondvc',
                kind='mysql')

    paths.build('~/PychronDev')
    meta_name = 'NMGRLMetaData'
    dvc = DVC(bind=False,
              organization='NMGRLData',
              meta_repo_name=meta_name)
    paths.meta_root = os.path.join(paths.dvc_dir, dvc.meta_repo_name)
    dvc.db.trait_set(**conn)
    if not dvc.initialize():
        warning(None, 'Failed to initialize DVC')
        return

    dvc.meta_repo.smart_pull()
    return dvc


def get_runlist():
    runlist = [('bu-FC-J-{}'.format(i), i) for i in range(4389, 4439)]
    return runlist


def fix_timestamp():
    dvc = get_dvc()
    dvc.connect()
    dvc.create_session()
    runlist = get_runlist()
    for run, aliquot in runlist:
        an = dvc.get_analysis_runid('bu-FC-J', aliquot)
        print('ff', an, an.repository_identifier)

        p = analysis_path(run, 'Streck2015')
        ip = analysis_path(run, 'Irradiation-NM-276')
        print(p, os.path.isfile(p), os.path.isfile(ip))
        # print('run {}'.format(run))


if __name__ == '__main__':
    paths.build('~/PychronDev')
    fix_timestamp()
# ============= EOF =============================================
