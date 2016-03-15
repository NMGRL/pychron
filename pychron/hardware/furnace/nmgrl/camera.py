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
from requests.exceptions import ConnectTimeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError
from traits.api import provides, Str
# ============= standard library imports ========================
import logging

from numpy import array
import requests
from PIL import Image
from cStringIO import StringIO
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
from pychron.hardware.core.i_core_device import ICoreDevice

logging.getLogger("requests").setLevel(logging.WARNING)


def timeout(func):
    def wrapper(obj, *args, **kw):
        try:
            return func(obj, *args, **kw)
        except ConnectTimeout:
            return False

    return wrapper


@provides(ICoreDevice)
class NMGRLCamera(ConfigLoadable):
    is_scanable = False
    host = Str

    def close(self):
        pass

    @timeout
    def test_connection(self):
        resp = requests.get('http://{}/html/cam_pic.php'.format(self.host), timeout=2)
        return resp.status_code == 200

    @timeout
    def get_image_data(self, size=None):
        resp = requests.get('http://{}/html/cam_pic.php'.format(self.host), timeout=2)
        if resp.status_code == 200:
            buf = StringIO(resp.content)
            buf.seek(0)
            im = Image.open(buf)
            # basewidth = 640
            # wpercent = (basewidth / float(im.size[0]))
            # hsize = int((float(im.size[1]) * float(wpercent)))
            if size:
                im = im.resize(size, Image.ANTIALIAS)

            return array(im)

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:
            if config.has_section('General'):
                name = self.config_get(config, 'General', 'name', optional=True)
                if name is not None:
                    self.name = name

            if config.has_section('Communications'):
                self.set_attribute(config, 'host', 'Communications', 'host', optional=False)
            return True

            # def open(self, *args, **kw):
            #     return HasCommunicator.open(self, *args, **kw)
            #
            # def get_image_data(self, size=None):
            #     imgstr = None
            #     timeout = 20
            #
            #     mf = MessageFrame()
            #     mf.nmessage_len = 8
            #     mf.message_len = True
            #     imgstr = self.communicator.ask('GetImageArray', message_frame=mf, delay=1)

            # with self.communicator.lock:
            # handler = self.communicator.get_handler()
            # handler.send_packet('GetImageArray')
            # time.sleep(0.05)
            # # self.communicator.tell('GetImageArray')
            # # self.communicator.reset()
            #
            # st = time.time()
            # nn = None
            # while 1:
            #     resp = handler.get_packet('GetImageArray')
            #     if resp:
            #         nn, resp = resp[:8], resp[8:]
            #         break
            #
            #     if time.time()-st > timeout:
            #         break
            #     # time.sleep(0.05)
            #
            # if nn is None:
            #     return
            #
            # st = time.time()
            # n = int(nn, 16)
            # self.debug('read nn={} n={}'.format(nn, n))
            # plen = None
            # while 1:
            #     resp += self.communicator.read()
            #     lresp = len(resp)
            #     if lresp >= n:
            #         imgstr = resp
            #         break
            #
            #     if lresp == plen:
            #         imgstr = resp
            #         break
            #     plen = lresp
            #
            #     if time.time()-st > timeout:
            #         break
            #     # time.sleep(0.05)

            # if imgstr:
            #     print len(imgstr)
            #     return loads(imgstr)

            # img = self.ask('GetImageArray')
            # if img is not None:
            #     img = fromstring(img)
            #     print img.shape
            #     return img

# ============= EOF =============================================
