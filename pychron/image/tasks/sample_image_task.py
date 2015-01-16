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
from traits.api import Event
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.envisage.browser.record_views import SampleRecordView
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
    save_event = Event

    def __init__(self, *args, **kw):
        super(SampleImageTask, self).__init__(*args, **kw)
        if self.manager:
            self.tool_bars[0].items.append(DBSnapshotAction())
        self.camera = ToupCamCamera()
        self.filter_non_run_samples = False

    # actions
    def save_file_snapshot(self):
        from pychron.core.helpers.filetools import unique_path2

        p,_ = unique_path2(paths.sample_image_dir, 'nosample', extension='.jpg')
        # self.camera.save(p)
        self.save_event = p

    def save_db_snapshot(self):
        if not self.selected_samples:
            self.warning_dialog('Please select a sample')
            return

        sample = self.selected_samples[0]
        self.info('adding image to sample. name={}, identifier={}'.format(sample.name, sample.identifier))

        p = os.path.join(paths.hidden_dir, 'temp_image.jpg')
        # self.save_event = p

        db = self.manager.db

        img = self.camera.get_image_data()

        # s = img.shape
        # from PySide.QtGui import QImage, QPixmap
        # img = QImage(img, s[1], s[0], QImage.Format_RGB32)
        # img.save(p, format='jpeg', quality=50)
        #
        # # self.camera.save(p)
        #
        # with open(p, 'r') as fp:
        db.add_sample_image(sample.name, img.tobytes(), identifier=sample.identifier)

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

    def _selected_projects_changed(self, old, new):
        if new and self.project_enabled:

            names = [ni.name for ni in new]
            self.debug('selected projects={}'.format(names))

            # self._load_associated_labnumbers(names)
            self._load_associated_samples(names)

            self.dump_browser_selection()

    def _load_associated_samples(self, names):
        db = self.manager.db
        with db.session_ctx():
            samples = db.get_samples(names)
            self.debug('get samples n={}'.format(len(samples)))

            def func(li, prog, i, n):
                if prog:
                    prog.change_message('Loading Sample {}'.format(li.name))

                if li.labnumbers:
                    return [SampleRecordView(li, identifier=ll.identifier) for ll in li.labnumbers]
                else:
                    return SampleRecordView(li)

            samples = progress_loader(samples, func)

        self.samples = samples
        self.osamples = samples

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem(id='pychron.image.browser'))
# ============= EOF =============================================



