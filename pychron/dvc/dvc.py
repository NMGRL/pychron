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

from git import Repo
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class DVC(Loggable):
    db = Instance('pychron.dvc.dvc_database.DVCDatabase', ())
    meta_repo = Instance('pychron.dvc.meta_repo.MetaRepo', ())

    def get_project(self, name):
        return self.db.get_project(name)

    def get_sample(self, name, project):
        return self.db.get_sample(name, project)

    def get_material(self, name):
        return self.db.get_material(name)

    def add_material(self, name):
        self.db.add_material(name)

    def add_sample(self, name, project, material):
        self.db.add_sample(name, project, material)

    def add_project(self, name):
        with self.db.session_ctx():
            self.db.add_project(name)

        p = os.path.join(paths.project_dir, name)
        os.mkdir(p)
        repo = Repo.init(p)

        # setup remotes


# ============= EOF =============================================



