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
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.paths import paths


class ImagePlugin(BaseTaskPlugin):
    id = 'pychron.image.plugin'
    name = 'Image'
    # watcher = Instance('pychron.image.watcher.DirectoryWatcher')

    # def start(self):
    #     """
    #     start a directory watcher
    #     monitors a directory for new image files
    #
    #     if the name of the image matches a sample name in the database
    #         save image to db and associate with sample
    #     else
    #         add name to a list and allow user to manually associate with a sample now or at a later time
    #
    #     :return:
    #     """
    #
    #     db = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
    #     if db:
    #         from pychron.image.watcher import DirectoryWatcher
    #
    #         dw = DirectoryWatcher(paths.sample_image_dir)
    #         dw.on_trait_change(self._handle_new_images, 'dir_changed', dispatch='ui')
    #         dw.start()
    #         self.watcher = dw
    #     else:
    #         self.warning('Database plugin not available')
    #
    # def _handle_new_images(self, new):
    #     if new:
    #         win, task, state = self.application.get_open_task('pychron.image.uploader')
    #         if not state:
    #             win.open()
    #
    #         task.handle_new_images(new)

    def _sample_image_factory(self):
        from pychron.image.tasks.sample_image_task import SampleImageTask

        man = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        s = SampleImageTask(manager=man)
        return s

    # def _upload_image_factory(self):
    #     from pychron.image.tasks.upload_task import ImageUploadTask
    #
    #     man = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
    #     s = ImageUploadTask(manager=man)
    #     return s

    def _tasks_default(self):
        ts = [TaskFactory(factory=self._sample_image_factory,
                          id='pychron.image.sample_imager',
                          name='Sample Imager')]

        # if self.application.get_plugin('pychron.database'):
        #     ts.append(TaskFactory(factory=self._upload_image_factory,
        #                           id='pychron.image.uploader',
        #                           name='Image Uploader'))

        return ts

# ============= EOF =============================================



