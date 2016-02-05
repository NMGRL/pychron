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
from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
from threading import Thread
import json
import os
import socket
import select
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class PsychoDramaCommandServer(Loggable):
    path = Str
    _listen = False
    _status_msg = 'No Status'

    def start(self):
        prefix = 'pychron.psychodrama'
        bind_preference(self, 'path', '{}.path'.format(prefix))

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.unlink(self.path)
        except OSError:
            pass

        sock.bind(self.path)

        self._listen = True

        t = Thread(target=self._listen, args=(sock,))
        t.setDaemon(True)
        t.start()

    def _listen(self, sock):

        _input = [sock]
        while self._listen:
            try:
                self._stream_listener(_input, sock)
            except Exception, err:
                self.debug('Listener Exception {}'.format(err))
                import traceback

                tb = traceback.format_exc()
                self.debug(tb)

    def _stream_listener(self, isock, sock):
        try:
            ins, _, _ = select.select(isock, [], [], 5)

            for s in ins:
                if s == sock:
                    client, _addr = sock.accept()
                    isock.append(client)
                else:
                    data = self._read(s)
                    if data:
                        self._process(s, data)
                    else:
                        s.close()
                        isock.remove(s)
        except select.error:
            pass

    def _read(self, sock):
        data = sock.recv(4096)
        l = 2
        if data:
            mlen = int(data[:l], 16)
            while len(data) < (mlen + l):
                data += sock.recv(4096)

            try:
                return json.loads(data)
            except BaseException, e:
                return 'Error loading json: {}'.format(e)

    def _process(self, sock, data):
        resp = self._process_request(data)
        self._end_request(sock, resp)

    def _process_request(self, data):
        if isinstance(data, str):
            return data

        try:

            auth_err = self._authenticate(data)
            if auth_err:
                return auth_err

            command = data['command']
            func = getattr(self, '_{}'.format(command))
            return func(data)

        except Exception, err:
            import traceback

            tb = traceback.format_exc()
            self.debug(tb)

            err = 'Process request Exception {}'.format(err)
            self.debug('Process request Exception {}'.format(err))
            traceback.print_exc()
            return err

    def _end_request(self, sock, data):
        try:
            func = lambda x: sock.sendto(x, self.path)

            mlen = len(data)
            totalsent = 0
            while totalsent < mlen:
                try:
                    totalsent += func(data[totalsent:])
                    # self.debug('totalsent={} n={}'.format(totalsent, mlen))
                except socket.error:
                    continue

        except Exception, err:
            self.debug('End Request Exception: {}'.format(err))

    def _authenticate(self, data):
        return True

    # commands
    def _status(self, data):
        return self._status_msg

    def _result(self, data):
        return self._result_msg

    def _run_experiment(self, data):
        exp = self.application.get_service('pychron.experiment.task')
        if exp is None:
            return 'No Experiment Plugin'

        def func():
            p = data['path']
            self._status_msg = 'Experiment started {}'.format(p)
            exp.open(data['path'])
            exp.execute()
            self._result_msg = 'OK'

        t = Thread(target=func)
        t.start()
        t.setDaemon(True)
        return 'Experiment Started'

# ============= EOF =============================================



