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
from pychron.core.yaml import yload

try:
    from pypylon import pylon, genicam
except ImportError:
    print('failed importing basler pylon')

import os

from pychron.loggable import Loggable


class BaslerPylonCamera(Loggable):
    def __init__(self, identifier, *args, **kw):

        # available_cameras = pypylon.factory.find_devices()
        factory = pylon.TlFactory.GetInstance()
        available_cameras = factory.EnumerateDevices()
        self.debug('Available cameras {}'.format(available_cameras))
        try:
            try:
                dev = available_cameras[int(identifier)]
            except ValueError:
                dev = next((c for c in available_cameras if c.user_defined_name == identifier), None)
            cam = pylon.InstantCamera(factory.CreateDevice(dev))
            # cam = pypylon.factory.create_device(dev)
        except (IndexError, NameError):
            cam = None
        self._cam = cam

        self.pixel_depth = 255
        self._grabber = None
        self._setting_config = False
        super(BaslerPylonCamera, self).__init__(*args, **kw)

    def open(self):
        if self._cam:
            self._cam.Open()
            self._cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            return True

    def load_configuration(self, cfg):
        self.debug('Load configuration')

        if cfg and self._cam:
            if not self._cam.IsOpen():
                self._cam.Open()

            self._cam.StopGrabbing()
            dev = cfg.get('Device')
            if dev:

                for k, v in dev.get('PylonParameters', {}).items():
                    try:
                        setattr(self._cam, k, v)
                        self.debug('Set {} to {}'.format(k, v))
                    except ValueError as e:
                        self.warning('Invalid Property value. k="{}",v={}. e={}'.format(k, v, e))
                    except KeyError:
                        self.warning('Invalid Camera Property "{}"'.format(k))
                    except RuntimeError as e:
                        self.warning('RunTimeError: {}. k={},v={}'.format(e, k, v))
                    except IOError as e:
                        self.warning('IOError: {}, k={}, v={}'.format(e, k, v))
                    except genicam.AccessException as e:
                        self.warning('Access Exception {}'.format(e))
                    except genicam.LogicalErrorException as e:
                        self.warning('Logical Error Exception {}'.format(e))

            self.pixel_depth = self._cam.PixelDynamicRangeMax.Value
            self._cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    def read(self):
        ok, img = False, None
        if self._cam and not self._setting_config:
            res = self._cam.RetrieveResult(0, pylon.TimeoutHandling_Return)
            if res.IsValid():
                ok = True
                img = res.Array
            res.Release()

        return ok, img

            # img = self._cam.grab_one()
            # return True, img

            # if self._grabber is None:
            #     self._grabber = self._cam.grab_images(-1, 1)
            #
            # try:
            #     img = next(self._grabber)
            #     return True, img
            # except (StopIteration, RuntimeError, ValueError) as e:
            #     self._grabber = None
            #     print('read', e)
            #     return False, None

    def release(self):
        self._cam.Close()

    def reload_configuration(self, p):

        # if self._cam:
        #     self._cam.stop_grabbing()
        #     self._grabber = None
        #
        # self._setting_config = True

        if os.path.isfile(p):
            yd = yload(p)
            self.load_configuration(yd)
        # self._setting_config = False