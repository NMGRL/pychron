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
from threading import Thread

import picamera
import picamera.array
# ============= standard library imports ========================
# ============= local library imports  ==========================
import time

from pychron.core.helpers.filetools import unique_path2
from pychron.headless_config_loadable import HeadlessConfigLoadable
from pychron.paths import paths


class RPiCamera(HeadlessConfigLoadable):

    sharpness = 0
    contrast = 0
    brightness = 50
    saturation = 0
    ISO = 0
    video_stabilization = False
    exposure_compensation = 0

    # exposure modes
    # off, auto, night, nightpreview, backlight, spotlight, sports, snow, beach,
    # verylong, fixedfps, antishake, fireworks,
    exposure_mode = 'auto'

    meter_mode = 'average'  # stop, average, backlit, matrix

    # awb_modes
    # off, auto, sunlight, cloudy, shade, tungsten, fluorescent, incandescent, flash, horizon
    awb_mode = 'auto'

    # image effects
    # none, negative, solarize, sketch, denoise, emboss, oilpaint, hatch,
    # gpen, pastel, watercolor,film, blur, saturation, colorswap, washedout,
    # posterise, colorpoint, colorbalance, cartoon, deinterlace1, deinterlace2
    image_effect = 'none'

    color_effects = None # (u,v)
    rotation = 0  # 0,90,180,270
    hflip = False
    vflip = False
    crop = (0.0, 0.0, 1.0, 1.0)

    frame_rate = 10

    def load_additional_args(self, *args, **kw):
        config = self.get_configuration()

        self.set_attribute(config, 'sharpness', 'Settings', 'sharpness', cast='int')
        self.set_attribute(config, 'contrast', 'Settings', 'contrast', cast='int')
        self.set_attribute(config, 'brightness', 'Settings', 'brightness', cast='int')
        self.set_attribute(config, 'saturation', 'Settings', 'saturation', cast='int')
        self.set_attribute(config, 'ISO', 'Settings', 'ISO', cast='int')
        self.set_attribute(config, 'video_stabilization', 'Settings', 'video_stabilization', cast='boolean')
        self.set_attribute(config, 'exposure_compensation', 'Settings', 'exposure_compensation', cast='int')
        self.set_attribute(config, 'exposure_mode', 'Settings', 'exposure_mode')
        self.set_attribute(config, 'meter_mode', 'Settings', 'meter_mode')
        self.set_attribute(config, 'awb_mode', 'Settings', 'awb_mode')
        self.set_attribute(config, 'image_effect', 'Settings', 'image_effect')
        self.set_attribute(config, 'color_effects', 'Settings', 'color_effects')
        self.set_attribute(config, 'rotation', 'Settings', 'rotation', cast='int')
        self.set_attribute(config, 'hflip', 'Settings', 'hflip', cast='boolean')
        self.set_attribute(config, 'vflip', 'Settings', 'vflip', cast='boolean')

        crop = self.config_get(config, 'Settings', 'crop')
        if crop:
            self.crop = tuple(map(float, crop.split(',')))

        return True

    def start_video_service(self):
        def func():
            root = '/www/firm_cam'
            if not os.path.isdir(root):
                os.mkdir(root)
            path = os.path.join(root, 'image.jpg')
            self.capture(path, setup=False)
            while 1:
                self.capture(path, setup=False)
                time.sleep(1/float(self.frame_rate))

        t = Thread(target=func)
        t.setDaemon(True)
        t.start()

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
        attrs = ('sharpness', 'contrast', 'brightness', 'saturation', 'ISO',
                 'video_stabilization', 'exposure_compensation', 'exposure_mode',
                 'meter_mode', 'awb_mode', 'image_effect', 'color_effects',
                 'rotation', 'hflip', 'vflip', 'crop')
        for attr in attrs:
            setattr(camera, attr, getattr(self, attr))


# ============= EOF =============================================
