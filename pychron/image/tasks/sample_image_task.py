# ===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.tasks.task_layout import TaskLayout, PaneItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.envisage.tasks.base_task import BaseManagerTask
# from pychron.image.camera import Camera
from pychron.image.tasks.actions import SnapshotAction, DBSnapshotAction
# from pychron.image.tasks.image_pane import SampleImagePane
from pychron.image.tasks.pane import SampleBrowserPane, CameraPane
from pychron.image.tasks.video_pane import VideoPane
from pychron.image.toupcam.camera import ToupCamCamera
from pychron.paths import paths


class SampleImageTask(BaseManagerTask, BrowserMixin):
    name = 'Sample Imager'
    id = 'pychron.image.sample_imager'

    tool_bars = [SToolBar(SnapshotAction())]

    def __init__(self, *args, **kw):
        super(SampleImageTask, self).__init__(*args, **kw)
        if self.manager:
            self.tool_bars[0].items.append(DBSnapshotAction())
        self.camera = ToupCamCamera()

    # actions
    def save_file_snapshot(self):
        from pychron.core.helpers.filetools import unique_path2

        p,_ = unique_path2(paths.sample_image_dir, 'nosample', extension='.jpg')
        self.camera.save(p)

    def save_db_snapshot(self):
        if not self.selected_samples:
            self.warning_dialog('Please select a sample')
            return

        sample = self.selected_samples[0]
        self.info('adding image to sample {}'.format(sample.identifier))

    # task interface
    def activated(self):
        self.camera.open()
        self.load_projects(include_recent=False)

    def prepare_destroy(self):
        self.camera.close()

    def create_central_pane(self):
        return CameraPane(model=self)

    def create_dock_panes(self):
        return [SampleBrowserPane(model=self)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem(id='pychron.image.browser'))
# ============= EOF =============================================



