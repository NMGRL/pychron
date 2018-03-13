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
from __future__ import absolute_import
from __future__ import print_function
import os
try:
    import pypylon
except ImportError:
    print('failed importing pylon')

import yaml
import six


from pychron.loggable import Loggable


class PylonCamera(Loggable):

    def __init__(self, identifier, *args, **kw):
        # Grep the first one and create a camera for it
        try:
            available_cameras = pypylon.factory.find_devices()
            self.debug('Available cameras {}'.format(available_cameras))
            cam = pypylon.factory.create_device(available_cameras[identifier])
        except (IndexError, NameError):
            cam = None
        self._cam = cam
        self.pixel_depth = 255
        self._grabber = None
        self._setting_config = False
        super(PylonCamera, self).__init__(*args, **kw)

    def open(self):
        if self._cam:
            self._cam.open()
            return True

    def load_configuration(self, cfg):
        self.debug('Load configuration')

        if cfg and self._cam:
            dev = cfg.get('Device')
            if dev:
                pylon = dev.get('PylonParameters', {})
                for k, v in pylon.items():
                    try:
                        self._cam.properties[k] = v
                        self.debug('Set {} to {}'.format(k, v))
                    except KeyError:
                        self.warning('Invalid Camera Property "{}"'.format(k))
                    except RuntimeError as e:
                        self.warning('RunTimeError: {}. k={},v={}'.format(e, k, v))
                    except IOError as e:
                        self.warning('IOError: {}, k={}, k={}'.format(e, k, v))
            self.pixel_depth = self._cam.properties['PixelDynamicRangeMax']

    def read(self):

        if self._cam and not self._setting_config:
            # img = self._cam.grab_one()

            # return True, img
            if self._grabber is None:
                self._grabber = self._cam.grab_images(-1, 1)

            try:
                img = next(self._grabber)
                return True, img
            except (StopIteration, RuntimeError, ValueError) as e:
                self._grabber = None
                print('read', e)
                return False, None

    def release(self):
        self._cam.close()

    def reload_configuration(self, p):
        if self._cam:
            self._cam.stop_grabbing()
            self._grabber = None

        self._setting_config = True
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                yd = yaml.load(rfile)
                self.load_configuration(yd)
        self._setting_config = False
# ============= EOF =============================================
