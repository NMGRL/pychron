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
import os
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
import shutil
from traits.api import HasTraits, Button, Str, List, Property, Bool
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.envisage.tasks.base_task import BaseTask, BaseManagerTask
from pychron.image.tasks.actions import AssociateAction, SaveAction
from pychron.image.tasks.pane import SampleBrowserPane
from pychron.image.tasks.upload_pane import UploadPane
from pychron.loggable import Loggable
from pychron.paths import paths


class UploadItem(HasTraits):
    name = Str
    sample = Str


class ImageUploadTask(BaseManagerTask, BrowserMixin):
    id = 'pychron.image.upload'
    name = 'Image Uploader'
    tool_bars = [SToolBar(AssociateAction(),
                          SaveAction())]
    items = List
    selected_items = List

    # association_enabled = Property(depends_on='selected_items[]')
    association_enabled = Bool

    def handle_new_images(self, new):
        if new:
            for ni in new:
                name = os.path.basename(ni)
                self.debug('Adding {} to database'.format(name))
                self.items.append(UploadItem(name=name))

                # move file out of staging area
                shutil.move(ni, os.path.join(paths.sample_image_backup_dir, name))

    # actions
    def save(self):
        self.debug('save associations')


    def associate_sample(self):
        self.debug('associate sample')
        sample = self.selected_samples[0].name
        print type(self.selected_samples[0])
        for si in self.selected_items:
            si.sample = sample
            print si.name, si.sample

    # task interface
    def activated(self):
        self.load_projects(include_recent=False)

    def prepare_destroy(self):
        pass

    def create_central_pane(self):
        return UploadPane(model=self)

    def create_dock_panes(self):
        return [SampleBrowserPane(model=self)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem(id='pychron.image.browser'))

    def _selected_samples_changed(self):
        self._set_association_enabled()

    def _selected_items_changed(self):
        self._set_association_enabled()

    def _set_association_enabled(self):

        self.association_enabled = bool(self.selected_items and
                                        len(self.selected_samples) == 1
                                        if self.selected_samples else False)

# ============= EOF =============================================



