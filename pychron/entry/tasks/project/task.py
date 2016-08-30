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
# ============= local library imports  ==========================
from pychron.entry.tasks.project.panes import ProjectPane
from pychron.entry.tasks.project.project_manager import ProjectManager
from pychron.envisage.tasks.base_task import BaseManagerTask


class ProjectTask(BaseManagerTask):
    name = 'Project Database'
    id = 'pychron.entry.project.task'

    def activated(self):
        self.manager.activated()

    def create_central_pane(self):
        return ProjectPane(model=self.manager)

    def _manager_default(self):
        dvc = self.application.get_service('pychron.dvc.dvc.DVC')
        dvc.connect()
        return ProjectManager(application=self.application, dvc=dvc)

# ============= EOF =============================================
