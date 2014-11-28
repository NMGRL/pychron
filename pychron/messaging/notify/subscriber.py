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
from threading import Thread, Event
import time

from traits.api import Str, Int, List, Float
import zmq

from pychron.loggable import Loggable



#============= standard library imports ========================
#============= local library imports  ==========================

class Subscriber(Loggable):
    host = Str
    port = Int

    _stop_signal = None
    _subscriptions = List
    was_listening = False
    verbose = True

    last_message_time = Float

    _request_sock = None
    _sock = None
    _poll = None

    def connect(self, timeout=None):
        context = zmq.Context()
        sock = context.socket(zmq.SUB)

        url = self._get_url()
        self.info('Connecting to {}'.format(url))

        sock.connect(url)
        self._sock = sock

        url = self._get_url(1)
        return self._check_server_availability(url, timeout, context=context)

    def _get_url(self, offset=0):
        h, p = self.host, self.port + offset
        return 'tcp://{}:{}'.format(h, p)

    def check_server_availability(self, timeout=1, verbose=True):
        url = self._get_url(1)
        return self._check_server_availability(url, timeout=timeout, verbose=verbose)

    def _check_server_availability(self, url, timeout=3, context=None, verbose=True):
        ret = True
        if timeout:

            resp = self.request('ping', timeout, context)

            if resp is None or resp != 'echo':
            #if not socks.get(alive_sock) == zmq.POLLIN or not alive_sock.recv()=='echo':
                if verbose:
                    self.warning('subscription server at {} not available'.format(url))
                    #sock.setsockopt(zmq.LINGER, 0)
                #alive_sock.close()
                #poll.unregister(alive_sock)
                ret = False

        return ret

    def request(self, msg, timeout=1, context=None):
        if context is None:
            context = zmq.Context()

        req_sock = self._request_sock
        if req_sock is None:
            url = self._get_url(1)
            req_sock = context.socket(zmq.REQ)
            req_sock.connect(url)
            self._request_sock = req_sock

        poll = self._poll
        if poll is None:
            poll = zmq.Poller()
            poll.register(req_sock, zmq.POLLIN)

        req_sock.send(msg)

        socks = dict(poll.poll(timeout * 1000))

        resp = None
        if socks.get(req_sock) == zmq.POLLIN:
            resp = req_sock.recv()
        else:
            req_sock.setsockopt(zmq.LINGER, 0)
            req_sock.close()
            poll.unregister(req_sock)
            self._request_sock = None

        return resp

    def subscribe(self, tag, cb, verbose=False):
        if self._sock:
            self.info('subscribing to {}'.format(tag))
            sock = self._sock
            sock.setsockopt(zmq.SUBSCRIBE, tag)
            self._subscriptions.append((tag, cb, verbose))

    def is_listening(self):
        return self._stop_signal and not self._stop_signal.is_set()

    def listen(self):
        self.info('starting subscriptions')
        self.was_listening = True

        self._stop_signal = Event()
        t = Thread(target=self._listen)
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.debug('stopping')
        if self._stop_signal:
            self._stop_signal.set()
            self.was_listening = False

    def _listen(self):
        sock = self._sock
        while not self._stop_signal.is_set():
            resp = sock.recv()
            if self.verbose:
                self.debug('raw notification {}'.format(resp))

            for si, cb, verbose in self._subscriptions:
                if resp.startswith(si):
                    resp = resp.split(si)[-1].strip()
                    if verbose:
                        self.info('received notification {}'.format(resp))
                    cb(resp)
                    self.last_message_time = time.time()
                    break

        self.debug('no longer listening {}'.format(self._stop_signal.is_set()))

# ============= EOF =============================================
