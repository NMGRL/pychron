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

from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import List, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.tasks.panes import RepoCentralPane, SelectionPane
from pychron.envisage.tasks.base_task import BaseTask
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import Organization
from pychron.paths import paths


class ExperimentRepoTask(BaseTask):
    name = 'Experiment Repositories'

    selected_repository_name = Str
    repository_names = List
    organization = Str

    local_names = List

    def activated(self):
        self._preference_binder('pychron.dvc', ('organization',))
        org = Organization(self.organization)
        self.repository_names = org.repos

        ns = []
        for i in os.listdir(paths.experiment_dataset_dir):
            if i.startswith('.'):
                continue

            root = os.path.join(paths.experiment_dataset_dir, i)
            if os.path.isdir(root):
                ns.append(i)

        self.local_names = ns

    def _selected_repository_name_changed(self, new):
        if new:
            root = os.path.join(paths.experiment_dataset_dir, new)
            if os.path.isdir(root):
                repo = GitRepoManager()
                repo.open_repo(root)

    def create_central_pane(self):
        return RepoCentralPane(model=self)

    def create_dock_panes(self):
        return [SelectionPane(model=self)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.repo.selection'))
# ============= EOF =============================================



