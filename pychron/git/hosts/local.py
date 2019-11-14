# ===============================================================================
# Copyright 2019 ross
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

from git import Repo

from pychron.git.hosts import BaseGitHostService
from pychron.paths import paths


class LocalGitHostService(BaseGitHostService):


    def create_repo(self, name, **kw):
        self.create_empty_repo(name)
        return True

    def create_empty_repo(self, name):
        root = paths.repository_dataset_dir
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            os.mkdir(p)
            repo = Repo.init(p)

    def get_repository_names(self, organization):
        root = paths.repository_dataset_dir
        names = [n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n))]
        return names

    def get_repos(self, organization):
        names = self.get_repository_names(organization)
        repos = [{'name': n} for n in names]
        return repos

# ============= EOF =============================================
