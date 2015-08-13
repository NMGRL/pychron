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
import os
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import create_organization_repository


def create_remote(root, name='origin', baseurl='https://github.com', organization='NMGRLData'):
    reponame = os.path.basename(root)
    create_organization_repository(organization, reponame,
                                   os.environ.get('GITHUB_USER'),
                                   os.environ.get('GITHUB_PWD'))
    repo = GitRepoManager()
    repo.open_repo(root)
    url = '{}/{}/{}.git'.format(baseurl, organization, reponame)
    repo.create_remote(url)
    print 'create repo at github {}'.format(url)

    repo._repo.git.add('.')
    print 'repo add'

    repo._repo.git.commit('-m', '<IMPORT> src=mysql://pychrondata@129.138.12.160')
    print 'repo commit'

    repo.push()
    print 'repo push'


if __name__ == '__main__':
    # for p in ('Irradiation-NM-258', 'Irradiation-NM-259', 'Irradiation-NM-260', 'Irradiation-NM-261'):
    for p in ('Irradiation-NM-266', 'Irradiation-NM-267', 'Irradiation-NM-268', 'Irradiation-NM-269'):
        ro = os.path.join('/Users/ross/Pychron_dev/data/.dvc/experiments', p)
        print 'create repo {}'.format(ro)
        create_remote(ro)

# ============= EOF =============================================
