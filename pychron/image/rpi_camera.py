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
import picamera
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2
from pychron.headless_config_loadable import HeadlessConfigLoadable
from pychron.paths import paths


class RPiCamera(HeadlessConfigLoadable):
    hflip = False
    vflip = False

    def load_additional_args(self, *args, **kw):
        config = self.get_configuration()

        self.set_attribute(config, 'hflip', 'General', 'hflip', cast='boolean')
        self.set_attribute(config, 'vflip', 'General', 'vflip', cast='boolean')
        return True

    def get_image_array(self):
        with picamera.PiCamera() as camera:
            self._setup_camera(camera)
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output, 'rgb')
                return output.array

    def capture(self, path=None, name=None, **options):
        with picamera.PiCamera() as camera:
            self._setup_camera(camera)
            if path is None:
                if name is None:
                    path, _ = unique_path2(paths.snapshot_dir, name, extension='.jpg')
                else:
                    path, _ = unique_path2(paths.snapshot_dir, 'rpi', extension='.jpg')

            camera.capture(path, **options)

    # private
    def _setup_camera(self, camera):
        camera.hflip = self.hflip
        camera.vflip = self.vflip

# ============= EOF =============================================
