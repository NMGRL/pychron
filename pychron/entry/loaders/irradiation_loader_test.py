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
import os
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.dvc.dvc import DVC
from pychron.entry.loaders.irradiation_loader import XLSIrradiationLoader
from pychron.paths import paths


def load_irradiation_file(p):
    paths.build('_dev')
    logging_setup('irrad_file', use_file=False, use_archiver=False)
    dvc = DVC(bind=False,
              organization='NMGRLData',
              meta_repo_name='MetaData',
              github_user=os.environ.get('GITHUB_USER'),
              github_password=os.environ.get('GITHUB_PWD'))

    paths.meta_root = os.path.join(paths.dvc_dir, dvc.meta_repo_name)

    dest_conn = dict(host='localhost',
                     username=os.environ.get('LOCALHOST_DB_USER'),
                     password=os.environ.get('LOCALHOST_DB_PWD'),
                     kind='mysql',
                     # echo=True,
                     name='pychrondvc_dev')

    dvc.db.trait_set(**dest_conn)
    if not dvc.initialize():
        print 'Failed to initialize DVC'
        return

    dvc.meta_repo.smart_pull()

    loader = XLSIrradiationLoader(db=dvc.db,
                                  dvc=dvc)
    loader.load_irradiation(p, dry_run=False)


if __name__ == '__main__':
    load_irradiation_file('/Users/ross/Sandbox/NM-281.xls')

# ============= EOF =============================================
