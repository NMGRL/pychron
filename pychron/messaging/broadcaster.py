# ===============================================================================
# Copyright 2016 ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from socket import gethostbyname, gethostname

import zmq

from pychron.headless_loggable import HeadlessLoggable


class Broadcaster(HeadlessLoggable):
    _sock = None
    _req_sock = None

    @property
    def url(self):
        host = gethostbyname(gethostname())
        return '{}:{}'.format(host, self.port)

    def setup(self, port):
        context = zmq.Context()
        self._setup_publish(context, port)

    def send_message(self, msg, verbose=True):
        if verbose:
            self.info('pushing message - {}'.format(msg))
        self._send(msg)

    # private
    def _setup_publish(self, context, port):
        sock = context.socket(zmq.PUB)
        sock.bind('tcp://*:{}'.format(port))
        self._sock = sock

    def _send(self, msg):
        with self._lock:
            if self._sock:
                try:
                    self._sock.send(msg)
                except zmq.ZMQBaseError, e:
                    self.warning('failed sending message: error {}: {}'.format(e, msg))
            else:
                self.debug('notifier not setup')

# ============= EOF =============================================
