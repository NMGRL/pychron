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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import TaskLayout, PaneItem, VSplitter

from pychron.entry.tasks.sample_prep.panes import SamplePrepPane, SamplePrepFilterPane, SamplePrepSessionPane
from pychron.entry.tasks.sample_prep.sample_prep import SamplePrep
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.pychron_constants import DVC_PROTOCOL


class LocateSampleAction(TaskAction):
    name = 'Locate Sample'
    method = 'locate_sample'


class SamplePrepTask(BaseManagerTask):
    name = 'Sample Prep'
    id = 'pychron.entry.sample.prep.task'

    tool_bars = [SToolBar(LocateSampleAction())]

    def activated(self):
        self.manager.activated()

    def prepare_destroy(self):
        self.manager.prepare_destroy()

    def create_central_pane(self):
        return SamplePrepPane(model=self.manager)

    def create_dock_panes(self):
        panes = [SamplePrepFilterPane(model=self.manager),
                 SamplePrepSessionPane(model=self.manager)]
        return panes

    def locate_sample(self):
        self.debug('locate sample')
        self.manager.locate_sample()

    def _manager_default(self):
        dvc = self.application.get_service(DVC_PROTOCOL)
        dvc.connect()
        return SamplePrep(application=self.application, dvc=dvc)

    def _default_layout_default(self):
        return TaskLayout(left=VSplitter(PaneItem('pychron.entry.sample.session'),
                                         PaneItem('pychron.entry.sample.filter')))

# ============= EOF =============================================
