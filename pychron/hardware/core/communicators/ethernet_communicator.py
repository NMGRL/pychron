# ===============================================================================
# Copyright 2011 Jake Ross
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
import socket
# ============= local library imports  ==========================
from communicator import Communicator
from pychron.globals import globalv
from pychron.loggable import Loggable


class Handler(Loggable):
    sock = None
    datasize = 2 ** 12

    use_message_len_checking = False

    def get_packet(self):
        pass

    def send_packet(self, p):
        pass

    def end(self):
        pass

    def _recvall(self, recv):
        ss = []
        sum = 0

        #disable message len checking
        msg_len = 1
        if self.use_message_len_checking:
            msg_len = 0

        while 1:
            s = recv(self.datasize)  #self._sock.recv(2048)
            if not s:
                break

            if not msg_len:
                msg_len = int(s[:4], 16)

            sum += len(s)
            ss.append(s)
            if sum >= msg_len:
                break
        data = ''.join(ss)

        if self.use_message_len_checking:
            #trim off header
            data = data[4:]
        return data


class TCPHandler(Handler):
    # datasize = 2 ** 10

    def open_socket(self, addr, timeout=2.0):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(addr)

    def get_packet(self, cmd):
        try:
            # ss=[]
            # sum = 0
            # msg_len=0
            # while 1:
            #     s = self._sock.recv(2048)
            #     if not msg_len:
            #         msg_len = int(s[:4],16)
            #
            #     sum+=len(s)
            #     ss.append(s)
            #     if sum==msg_len:
            #         break
            # data = ''.join(ss)
            #
            # #trim off header
            # return data[4:]
            return self._recvall(self.sock.recv)
        except socket.timeout:
            return

    def send_packet(self, p):
        self.sock.send(p)
        return True

    def end(self):
        self.sock.close()


class UDPHandler(Handler):
    # datasize = 2 ** 10

    def open_socket(self, addr, timeout=3.0):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.connect(addr)
        if globalv.communication_simulation:
            timeout = 0.01
        self.sock.settimeout(timeout)

    def get_packet(self, cmd):
        r = None
        #        cnt = 3
        cnt = 1

        def recv(ds):
            r, _ = self.sock.recvfrom(ds)
            return r

        for _ in range(cnt):
            try:
                r = self._recvall(recv)
                # r, _address = self.sock.recvfrom(self.datasize)
                break
            except socket.error, e:
                self.debug('get_packet {}'.format(e))
        else:
            self.warning('get packet for {} error: {}'.format(cmd, e))

        return r

    def send_packet(self, p):
        #        self.sock.sendto(p, self.address)
        ok = False
        try:
            self.sock.sendto(p, self.address)
            ok = True
        except socket.error, e:
            self.warning('send packet {} {}'.format(e, self.address))

        return ok


class EthernetCommunicator(Communicator):
    """
    """
    host = None
    port = None
    handler = None
    kind = 'UDP'
    test_cmd = '***'
    use_end = True
    verbose = False

    def load(self, config, path):
        """
        """
        super(EthernetCommunicator, self).load(config, path)

        self.host = self.config_get(config, 'Communications', 'host')
        # self.host = 'localhost'
        self.port = self.config_get(config, 'Communications', 'port', cast='int')

        self.kind = self.config_get(config, 'Communications', 'kind', optional=True)
        self.test_cmd = self.config_get(config, 'Communications', 'test_cmd', optional=True, default='***')
        self.use_end = self.config_get(config, 'Communications', 'use_end', cast='boolean', optional=True,
                                       default=False)

        if self.kind is None:
            self.kind = 'UDP'

        return True

    def open(self, *args, **kw):
        return self.test_connection()

    def test_connection(self):
        self.simulation = False

        handler = self.get_handler()
        # send a test command so see if wer have connection
        cmd = self.test_cmd
        if cmd:
            self.debug('sending test command {}'.format(cmd))
            if handler:
                if handler.send_packet(cmd):
                    r = handler.get_packet(cmd)
                    if r is None:
                        self.simulation = True
                else:
                    self.simulation = True
            else:
                self.simulation = True

        return not self.simulation

    def get_handler(self):
        if self.kind.lower() == 'udp':
            if self.handler is None:
                h = UDPHandler()
                h.open_socket((self.host, self.port))
            else:
                h = self.handler
        else:
            if self.handler is None:
                h = TCPHandler()
                try:
                    h.open_socket((self.host, self.port))
                except socket.error, e:
                    self.debug(str(e))
                    h = None

                self.handler = h
            else:
                h = self.handler
        return h

    def _reset_connection(self):
        self.handler = None

    def read(self, *args, **kw):
        handler = self.get_handler()
        return handler.get_packet('')

    def ask(self, cmd, retries=3, verbose=True, quiet=False, info=None, *args, **kw):
        """

        """

        if self.simulation:
            if verbose:
                self.info('no handle    {}'.format(cmd.strip()))
            return

        cmd = '{}{}'.format(cmd, self.write_terminator)

        def _ask():
            handler = self.get_handler()
            if not handler:
                self.simulation = True
                return

            if handler.send_packet(cmd):
                return handler.get_packet(cmd)

        r = None
        with self._lock:
            re = 'ERROR: Connection refused {}:{}'.format(self.host, self.port)
            # if self.simulation:
            #     return 'simulation'

            for _ in range(retries):
                r = _ask()
                if r is not None:
                    break
                else:
                    self._reset_connection()

        if r is not None:
            re = self.process_response(r)

        if self.use_end:
            handler = self.get_handler()
            handler.end()
            self._reset_connection()

        if verbose or self.verbose and not quiet:
            self.log_response(cmd, re, info)

        return r

    def tell(self, cmd, verbose=True, quiet=False, info=None):
        self._lock.acquire()
        handler = self.get_handler()

        if handler.send_packet(cmd):
            if verbose or self.verbose and not quiet:
                self.log_tell(cmd, info)
        self._lock.release()

# ============= EOF ====================================
