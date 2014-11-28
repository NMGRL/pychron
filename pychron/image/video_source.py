# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, File, Str, Int
#============= standard library imports ========================
import zmq
from cStringIO import StringIO
import Image as PILImage
import os
from numpy import asarray, array

#============= local library imports  ==========================
from pychron.image.image import Image
from pychron.image.cv_wrapper import resize


def parse_url(url):
    if url.startswith('file://'):
        r = url[7:]
        islocal = True
    else:
        islocal = False
        # strip off 'lan://'
        url = url[6:]
        if ':' in url:
            host, port = url.split(':')
        else:
            host = url
            port = 8080

        r = host, int(port)

    return islocal, r

class VideoSource(HasTraits):

    image_path = File
    host = Str('localhost')
    port = Int(1080)
    quality = Int

    _sock = None
    poller = None
    _cached_image = None

    def __init__(self, *args, **kw):
        super(VideoSource, self).__init__(*args, **kw)
        self.poller = zmq.Poller()
        self.reset_connection()

# ===============================================================================
# capture protocol
# ===============================================================================
    def release(self):
        pass

    def read(self):
        return True, self.get_image_data()

    def set_url(self, url):
        islocal, r = parse_url(url)
        if islocal:
            self.image_path = r
        else:
            self.host, self.port = r
            self.reset_connection()

    def reset_connection(self, clear_connection_count=True):
        if self._sock:
            try:
                self.poller.unregister(self._sock)
            except KeyError:
                pass
        context = zmq.Context()
        self._sock = context.socket(zmq.REQ)

        self._sock.connect('tcp://{}:{}'.format(self.host,
                                                  self.port))
#         self._sock.setsockopt(zmq.SUBSCRIBE, '')
        self.poller.register(self._sock, zmq.POLLIN)
        if clear_connection_count:
            self._no_connection_cnt = 0
        self._connected = True
        self._reset = True
        return self._sock


    def get_image_data(self, size=None):
        if self._sock is None:
            img = self._get_image_data()
        else:
            img = self._get_video_data()

        if img is not None:
            if size:
                img = resize(img, *size)
            return asarray(img[:, :])

    def _image_path_changed(self):
        if self.image_path:
            self._cached_image = Image.new_frame(self.image_path, swap_rb=True)

    def _quality_changed(self):
        resp = self._get_reply('QUALITY{}'.format(self.quality))

    def _get_reply(self, request, timeout=100):
        if not self._connected:
            return

        poll = self.poller
        client = self._sock
        try:
            client.send(request)
        except Exception:
            return

        socks = dict(poll.poll(timeout))
        if socks.get(client) == zmq.POLLIN:
            reply = client.recv()
            return reply

        else:
            client.setsockopt(zmq.LINGER, 0)
            client.close()
            poll.unregister(client)

            self._no_connection_cnt += 1
            if self._no_connection_cnt > 5:
                self._connected = False
                p = os.path.join(os.path.dirname(__file__), 'no_connection.jpg')
                self._cached_image = Image.new_frame(p,
                                                swap_rb=True)
            else:
                self.reset_connection(clear_connection_count=False)
                return self._get_reply(request, timeout)

    def _get_video_data(self):
        if self._connected:
            resp = self._get_reply('IMAGE')
            if resp:
                buf = StringIO(resp)
                buf.seek(0)
                img = PILImage.open(buf)
                img = img.convert('RGB')
                self._cached_image = array(img)

        return self._cached_image

    def _get_image_data(self):
        '''
            return ndarray
        '''
        img = self._cached_image
        if img is None:
            self._image_path_changed()

        return self._cached_image
# ============= EOF =============================================
