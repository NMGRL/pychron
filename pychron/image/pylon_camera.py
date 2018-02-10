# ===============================================================================
# Copyright 2018 ross
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
import os
import pypylon
import yaml


class PylonCamera:
    def __init__(self, identifier):
        available_cameras = pypylon.factory.find_devices()

        # Grep the first one and create a camera for it
        cam = pypylon.factory.create_device(available_cameras[identifier])
        # Open camera and grep some images
        self._cam = cam

    def load_configuration(self, cfg):
        # self._cam.properties['PixelFormat'] = 'Mono12'
        # self._cam.properties['GevSCPD'] = 1500
        if cfg:
            dev = cfg.get('Device')
            if dev:
                pylon = dev.get('PylonParameters', {})
                for k, v in pylon:
                    self._cam.properties[k] = v

    def read(self):
        img = self._cam.grab_image()
        return img
# ============= EOF =============================================
