#===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Button, Property, Bool, Int
from traitsui.api import View, Item, ButtonEditor
#============= standard library imports ========================
from threading import Thread, Event
import time
from numpy import array
#============= local library imports  ==========================
from pychron.image.video import Video
from pychron.loggable import Loggable
import zmq

class VideoServer(Loggable):
    video = Instance(Video)
    port = Int(1084)
    quality = Int(75)
    _started = False
    use_color = True
    start_button = Button
    start_label = Property(depends_on='_started')
    _started = Bool(False)
    def _get_start_label(self):
        return 'Start' if not self._started else 'Stop'

    def _start_button_fired(self):
        if self._started:
            self.stop()
        else:
            self.start()

    def traits_view(self):
        v = View(Item('start_button', editor=ButtonEditor(label_value='start_label')))
        return v

    def _video_default(self):
        return Video(swap_rb=True)

    def stop(self):
#        if self._started:
        self.info('stopping video server')
        self._stop_signal.set()
        self._started = False

    def start(self):
        self.info('starting video server')
        self._new_frame_ready = Event()
        self._stop_signal = Event()

        self.video.open(user='server')
        bt = Thread(name='broadcast', target=self._broadcast)
        bt.start()

        self.info('video server started')
        self._started = True

    def _broadcast(self):
#        new_frame = self._new_frame_ready
        self.info('video broadcast thread started')

        context = zmq.Context()
#         sock = context.socket(zmq.PUB)
        sock = context.socket(zmq.REP)
        sock.bind('tcp://*:{}'.format(self.port))

        poll = zmq.Poller()
        poll.register(sock, zmq.POLLIN)

        self.request_reply(sock, poll)
#        if use_color:
#            kw = dict(swap_rb=True)
#            depth = 3
#        else:
#            kw = dict(gray=True)
#            depth = 1

#         pt = time.time()

    def request_reply(self, sock, poll):
        stop = self._stop_signal
        video = self.video
        fps = 10
        import Image
        from cStringIO import StringIO
        quality = self.quality
        while not stop.isSet():

            socks = dict(poll.poll(100))
            if socks.get(sock) == zmq.POLLIN:
                resp = sock.recv()
                if resp == 'FPS':
                    buf = str(fps)
                elif resp.startswith('QUALITY'):
                    quality = int(resp[7:])
                    buf = ''
                else:
                    f = video.get_frame()

        #            new_frame.clear()

                    im = Image.fromarray(array(f))
                    s = StringIO()
                    im.save(s, 'JPEG', quality=quality)
                    buf = s.getvalue()

                sock.send(buf)


    def publisher(self, sock):
        stop = self._stop_signal
        video = self.video
        use_color = self.use_color
        fps = 10
        import Image
        from cStringIO import StringIO
        while not stop.isSet():

            f = video.get_frame(gray=False)
#            new_frame.clear()
            im = Image.fromarray(array(f))
            s = StringIO()
            im.save(s, 'JPEG')

            sock.send(str(fps))
            sock.send(s.getvalue())

            time.sleep(1.0 / fps)

# class VideoServer2(Loggable):
#    video = Instance(Video)
#    port = 5556
#
#    _frame = None
#
#    _new_frame_ready = None
#    _stop_signal = None
#
#
#    use_color = False
#    def _video_default(self):
#        v = Video()
#        return v
#
#
#
#    def stop(self):
#        if self._started:
#            self.info('stopping video server')
#            self._stop_signal.set()
#            self._started = False
#
#    def start(self):
#        if not self._started:
#            self.info('starting video server')
#            self._new_frame_ready = Event()
#            self._stop_signal = Event()
#
#            self.video.open(user='server')
#            bt = Thread(name='broadcast', target=self._broadcast, args=(
#                                                                        self.video,
#                                                                        self.use_color,
#                                                                        self._stop_signal,
#                                                                        self._new_frame_ready
#                                                                        ))
#            bt.start()
#
#            self._started = True
#            self.info('video server started')
#
#    def _broadcast(self, video, use_color, stop, new_frame):
#        self.info('video broadcast thread started')
#        import zmq
#        context = zmq.Context()
#        sock = context.socket(zmq.PUB)
#        sock.bind('tcp://*:{}'.format(self.port))
#        fp = 1 / 5.
#
#        if self.use_color:
#            kw = dict(swap_rb=True)
#            depth = 3
#        else:
#            kw = dict(gray=True)
#            depth = 1
#
#        while not stop.isSet():
#            t = time.time()
#
#            f = video.get_frame(**kw)
#
#            new_frame.clear()
#            w, h = f.size()
#            header = array([w, h, fp, depth])
# #            data = array([header.tostring(), f.ndarray.tostring()], dtype='str')
#            sock.send(header.tostring())
#            sock.send(f.ndarray.tostring())
#            time.sleep(max(0.001, fp - (time.time() - t)))


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('vs')
    s = VideoServer()
    s.configure_traits()
#    s.video.open(user='server')
#    s.start()

#============= EOF =============================================
