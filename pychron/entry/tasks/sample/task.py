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

import os

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem

from pychron.entry.tasks.sample.actions import DumpAction, LoadAction, RecoverAction
from pychron.entry.tasks.sample.actions import SaveAction
from pychron.entry.tasks.sample.panes import SampleEntryPane, SampleEditorPane
from pychron.entry.tasks.sample.sample_entry import SampleEntry
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.paths import paths
from pychron.pychron_constants import DVC_PROTOCOL


class SampleEntryTask(BaseManagerTask):
    name = 'Sample'
    id = 'pychron.entry.sample.task'
    tool_bars = [SToolBar(SaveAction()),
                 SToolBar(DumpAction(), LoadAction(), RecoverAction())]

    def activated(self):
        self.manager.activated()

    def prepare_destroy(self):
        self.manager.prepare_destroy()

    def create_central_pane(self):
        return SampleEntryPane(model=self.manager)

    def create_dock_panes(self):
        return [SampleEditorPane(model=self.manager)]

    # toolbar handlers
    def save(self):
        self.manager.save()

    def load(self):
        p = self.open_file_dialog(default_directory=paths.sample_dir)
        if p:
            self.manager.load(p)

    def recover(self):
        p = os.path.join(paths.sample_dir, '.last.yaml')
        if os.path.isfile(p):
            self.manager.load(p)

    def dump(self):
        p = self.save_file_dialog(default_directory=paths.sample_dir)
        # p = '/Users/ross/Sandbox/sample_entry.yaml'
        if p:
            self.manager.dump(p)

    # defaults
    def _manager_default(self):
        dvc = self.application.get_service(DVC_PROTOCOL)
        dvc.connect()
        return SampleEntry(application=self.application, dvc=dvc)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.entry.sample.editor'))

# ============= EOF =============================================
