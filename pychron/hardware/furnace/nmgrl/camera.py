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
from numpy import fromstring
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
from pychron.has_communicator import HasCommunicator


class NMGRLCamera(ConfigLoadable, HasCommunicator):

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:
            if config.has_section('General'):
                name = self.config_get(config, 'General', 'name', optional=True)
                if name is not None:
                    self.name = name

            if config.has_section('Communications'):
                comtype = self.config_get(config, 'Communications', 'type')
                if not self._load_communicator(config, comtype):
                    return False

            return True

    def open(self, *args, **kw):
        return HasCommunicator.open(self, *args, **kw)

    def get_image_data(self, size=None):
        imgstr = None
        with self.communicator.lock:
            self.communicator.tell('GetImageArray')
            resp = self.communicator.read()
            n, resp = resp[:2], resp[2:]
            while 1:
                resp += self.communicator.read()
                if len(resp) >=n:
                    imgstr = resp

        if imgstr:
            return fromstring(imgstr)

        # img = self.ask('GetImageArray')
        # if img is not None:
        #     img = fromstring(img)
        #     print img.shape
        #     return img

# ============= EOF =============================================



