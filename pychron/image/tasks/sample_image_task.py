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
from traits.api import Event, List, Instance
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.envisage.browser.base_browser_model import BaseBrowserModel
from pychron.envisage.browser.record_views import SampleRecordView, SampleImageRecordView
# from pychron.image.camera import Camera
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.image.tasks.actions import SnapshotAction, DBSnapshotAction, UploadAction
# from pychron.image.tasks.image_pane import SampleImagePane
from pychron.image.tasks.pane import SampleBrowserPane, InfoPane  # , CameraTabPane
from pychron.image.tasks.save_view import DBSaveView
from pychron.image.tasks.tab import CameraTab, ImageTabEditor, ImageModel
from pychron.image.toupcam.camera import ToupCamCamera
from pychron.paths import paths


class SampleImageTask(BaseEditorTask, BaseBrowserModel):
    name = 'Sample Imager'
    id = 'pychron.image.sample_imager'

    tool_bars = [SToolBar(SnapshotAction()),
                 SToolBar(UploadAction())]
    save_event = Event

    images = List
    selected_image = Instance(SampleImageRecordView)
    selected_info_model = Instance(ImageModel, ())
    dclicked = Event
    _prev_name = None

    def __init__(self, *args, **kw):
        super(SampleImageTask, self).__init__(*args, **kw)
        if self.manager:
            self.tool_bars[0].items.append(DBSnapshotAction())
        self.camera = ToupCamCamera()
        self.filter_non_run_samples = False

    def save(self, path=None):
        if self.active_editor and isinstance(self.active_editor, ImageTabEditor):
            if self.active_editor.dirty:
                db = self.manager.db
                with db.session_ctx():
                    dbim = db.get_sample_image(self.active_editor.record_id)
                    dbim.note = self.active_editor.model.note
                    dbim.name = self.active_editor.model.name
                    self.active_editor.model.original_note = dbim.note
                    self.active_editor.model.original_name = dbim.name
                self.active_editor.dirty = False

            self._load_associated_images(self.selected_samples)

    def save_as(self):
        self.save()

    # actions
    def upload_image_from_file(self):
        if not self.selected_samples:
            self.information_dialog('Please select a sample to associate with the image')
            return

        path = self.open_file_dialog(default_directory=os.path.expanduser('~'), wildcard='*.jpg|*.jpeg')
        if path is not None:
            with open(path, 'rb') as rfile:
                self.save_db_snapshot(rfile.read())

        self._load_associated_images(self.selected_samples)

    def save_file_snapshot(self):
        from pychron.core.helpers.filetools import unique_path2

        p, _ = unique_path2(paths.sample_image_dir, 'nosample', extension='.jpg')
        p, _ = unique_path2(paths.sample_image_dir, 'nosample', extension='.tiff')
        self.camera.save(p)

    def save_db_snapshot(self, blob=None):
        if not self.selected_samples:
            self.warning_dialog('Please select a sample')
            return

        sample = self.selected_samples[0]
        self.info('adding image to sample. name={}, identifier={}'.format(sample.name, sample.identifier))

        name = self._prev_name
        if not name:
            # get existing images for this sample
            db = self.manager.db
            with db.session_ctx():
                # sample = db.get_sample(sample.name, identifier=sample.identifier)
                cnt = db.get_sample_image_count(sample.name, project=sample.project,
                                                material=sample.material,
                                                identifier=sample.identifier)
                cnt += 1

            name = '{}{:03d}'.format(sample.name, cnt)

        v = DBSaveView(name=name)
        info = v.edit_traits()
        if info.result:
            self._prev_name = v.name
            self.debug('save image with name={}'.format(name))
            if blob is None:
                blob = self.camera.get_jpeg_data(quality=75)

            db.add_sample_image(sample.name, v.name, blob, v.note, identifier=sample.identifier)


    # task interface
    def activated(self):
        self.camera.open()

        editor = CameraTab(model=self,
                           name='Camera')

        self._open_editor(editor)
        self.load_projects(include_recent=False)

    def prepare_destroy(self):
        self.camera.close()

    def create_dock_panes(self):
        return [SampleBrowserPane(model=self),
                InfoPane(model=self)]

    def _selected_projects_changed(self, old, new):
        if new and self.project_enabled:
            names = [ni.name for ni in new]
            self.debug('selected projects={}'.format(names))

            # self._load_associated_labnumbers(names)
            self._load_associated_samples(names)

            self.dump_browser_selection()

    def _selected_samples_changed(self, new):
        if new:
            self._load_associated_images(new)

    # def _selected_image_changed(self, new):
    def _dclicked_changed(self):
        selected = self.selected_image
        if selected:
            db = self.manager.db
            with db.session_ctx():
                dbim = db.get_sample_image(selected.record_id)
                editor = self.get_editor(selected.record_id, key='record_id')
                if not editor:
                    model = ImageModel(blob=dbim.image,
                                       name=dbim.name,
                                       create_date=dbim.create_date,
                                       note=dbim.note or '')

                    editor = ImageTabEditor(record_id=selected.record_id,
                                            model=model,
                                            name=dbim.name)
                    self._open_editor(editor)
                else:
                    self.activate_editor(editor)

    def _active_editor_changed(self, new):
        if new and isinstance(new.model, ImageModel):
            self.selected_info_model = new.model

    def _load_associated_images(self, sample_records):
        db = self.manager.db
        with db.session_ctx():
            images = []
            for si in sample_records:
                sample = db.get_sample(si.name, si.project, si.material, si.identifier)
                images.extend([SampleImageRecordView(i) for i in sample.images])

        self.images = images

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
        return TaskLayout(left=PaneItem(id='pychron.image.browser'),
                          right=PaneItem(id='pychron.image.info'))

# ============= EOF =============================================



