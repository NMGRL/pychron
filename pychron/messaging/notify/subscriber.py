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

# ============= enthought library imports =======================
from __future__ import absolute_import

import time
from threading import Thread, Event

import zmq
from traits.api import Str, Int, List, Float, Bool

from pychron.loggable import Loggable


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Subscriber(Loggable):
    host = Str
    port = Int
    connection_state = Str("disconnected")
    config_loaded = Bool(False)
    stale_timeout = Float(10)
    last_heartbeat_time = Float

    _stop_signal = None
    _subscriptions = List
    was_listening = False
    verbose = True

    last_message_time = Float

    _request_sock = None
    _sock = None
    _poll = None
    _context = None
    _listen_thread = None

    def connect(self, timeout=None):
        self.close()
        context = zmq.Context()
        self._context = context
        self._sock = self._make_sub_socket(context)
        self.connection_state = "connecting"

        url = self._get_url(1)
        ok = self._check_server_availability(url, timeout, context=context)
        self.connection_state = "connected" if ok else "unavailable"
        return ok

    def _get_url(self, offset=0):
        h, p = self.host, self.port + offset
        return "tcp://{}:{}".format(h, p)

    def check_server_availability(self, timeout=1, verbose=True):
        url = self._get_url(1)
        return self._check_server_availability(url, timeout=timeout, verbose=verbose)

    def _check_server_availability(self, url, timeout=3, context=None, verbose=True):
        ret = True
        if timeout:
            resp = self.request("ping", timeout, context)

            if resp is None or resp != "echo":
                # if not socks.get(alive_sock) == zmq.POLLIN or not alive_sock.recv()=='echo':
                if verbose:
                    self.warning("subscription server at {} not available".format(url))
                    # sock.setsockopt(zmq.LINGER, 0)
                # alive_sock.close()
                # poll.unregister(alive_sock)
                ret = False

        return ret

    def request(self, msg, timeout=1, context=None):
        if context is None:
            context = self._context or zmq.Context()
            if self._context is None:
                self._context = context

        req_sock = self._request_sock
        if req_sock is None:
            req_sock = self._make_request_socket(context)

        poll = self._poll
        if poll is None:
            poll = zmq.Poller()
            poll.register(req_sock, zmq.POLLIN)
            self._poll = poll

        req_sock.send_string(msg)

        socks = dict(poll.poll(timeout * 1000))

        resp = None
        if socks.get(req_sock) == zmq.POLLIN:
            resp = req_sock.recv()
            self.connection_state = "connected"
        else:
            self.connection_state = "unavailable"
            self._close_request_socket()

        return resp

    def subscribe(self, tag, cb, verbose=False):
        if (tag, cb, verbose) not in self._subscriptions:
            self._subscriptions.append((tag, cb, verbose))
        if self._sock:
            self.info("subscribing to {}".format(tag))
            self._sock.setsockopt_string(zmq.SUBSCRIBE, tag)

    def is_listening(self):
        return self._stop_signal and not self._stop_signal.is_set()

    def listen(self):
        self.info("starting subscriptions")
        self.was_listening = True

        self._stop_signal = Event()
        self._listen_thread = Thread(target=self._listen)
        self._listen_thread.setDaemon(True)
        self._listen_thread.start()

    def stop(self):
        self.debug("stopping")
        if self._stop_signal:
            self._stop_signal.set()
            self.was_listening = False
        self.connection_state = "stopped"

    def close(self):
        self.stop()
        self._close_request_socket()
        if self._sock is not None:
            self._sock.setsockopt(zmq.LINGER, 0)
            self._sock.close()
            self._sock = None
        if self._context is not None:
            self._context.term()
            self._context = None
        self.connection_state = "disconnected"

    def _listen(self):
        poll = zmq.Poller()
        poll.register(self._sock, zmq.POLLIN)
        while not self._stop_signal.is_set():
            try:
                socks = dict(poll.poll(250))
            except zmq.ZMQBaseError:
                self.connection_state = "unavailable"
                break

            if socks.get(self._sock) == zmq.POLLIN:
                try:
                    resp = self._sock.recv_string()
                except zmq.ZMQBaseError:
                    self.connection_state = "unavailable"
                    break

                if self.verbose:
                    self.debug("raw notification {}".format(resp))

                self.connection_state = "connected"
                for si, cb, verbose in self._subscriptions:
                    if resp.startswith(si):
                        payload = resp.split(si, 1)[-1].strip()
                        if verbose:
                            self.info("received notification {}".format(payload))
                        cb(payload)
                        self.last_message_time = time.time()
                        break
            elif (
                self.last_heartbeat_time
                and time.time() - self.last_heartbeat_time > self.stale_timeout
            ):
                self.connection_state = "stale"

        self.debug("no longer listening {}".format(self._stop_signal.is_set()))

    def _make_sub_socket(self, context):
        sock = context.socket(zmq.SUB)
        url = self._get_url()
        self.info("Connecting to {}".format(url))
        sock.connect(url)
        for tag, _cb, _verbose in self._subscriptions:
            sock.setsockopt_string(zmq.SUBSCRIBE, tag)
        return sock

    def _make_request_socket(self, context):
        url = self._get_url(1)
        req_sock = context.socket(zmq.REQ)
        req_sock.connect(url)
        self._request_sock = req_sock
        return req_sock

    def _close_request_socket(self):
        if self._request_sock is not None:
            if self._poll is not None:
                try:
                    self._poll.unregister(self._request_sock)
                except KeyError:
                    pass
            self._request_sock.setsockopt(zmq.LINGER, 0)
            self._request_sock.close()
            self._request_sock = None
        self._poll = None


# ============= EOF =============================================
