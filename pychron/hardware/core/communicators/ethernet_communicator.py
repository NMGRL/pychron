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
from pychron.hardware.core.checksum_helper import computeCRC
from pychron.loggable import Loggable


class MessageFrame(object):
    def __init__(self, message_len=False, nmessage_len=4, checksum=False, nchecksum=4):
        self.nchecksum = nchecksum
        self.checksum = checksum
        self.nmessage_len = nmessage_len
        self.message_len = message_len

    def set_str(self, s):
        """
        L4,-,C4
        """
        args = s.split(',')
        if len(args) == 3:
            ml = args[0]
            cs = args[2]
            self.nmessage_len = int(ml[1:])
            self.nchecksum = int(cs[1:])
            self.checksum = True
            self.message_len = True


class Handler(Loggable):
    sock = None
    datasize = 2 ** 12
    address = None
    message_frame = None
    # use_message_len_checking = True
    # use_checksum = True

    def set_frame(self, f):
        self.message_frame = MessageFrame()
        self.message_frame.set_str(f)

    def get_packet(self, cmd):
        raise NotImplementedError

    def send_packet(self, p):
        raise NotImplementedError

    def end(self):
        pass

    def _recvall(self, recv):
        ss = []
        sum = 0

        # disable message len checking
        # msg_len = 1
        # if self.use_message_len_checking:
        # msg_len = 0

        msg_len = 1
        nm = -1
        frame = self.message_frame
        if frame.message_len:
            msg_len = 0
            nm = frame.nmessage_len

        while 1:
            s = recv(self.datasize)  # self._sock.recv(2048)
            if not s:
                break

            if not msg_len:
                msg_len = int(s[:nm], 16)

            sum += len(s)
            ss.append(s)
            if sum >= msg_len:
                break
        data = ''.join(ss)
        data = data.strip()
        if frame.message_len:
            # trim off header
            data = data[nm:]

        if frame.checksum:
            nc = frame.nchecksum
            checksum = data[-nc:]
            data = data[:-nc]
            comp = computeCRC(data)
            if comp != checksum:
                print 'checksum fail computed={}, expected={}'.format(comp, checksum)
                return

        return data


class TCPHandler(Handler):
    def open_socket(self, addr, timeout=1.0):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if globalv.communication_simulation:
            timeout = 0.01
        self.sock.settimeout(timeout)
        self.sock.connect(addr)

    def get_packet(self, cmd):
        try:
            return self._recvall(self.sock.recv)
        except socket.timeout:
            return

    def send_packet(self, p):
        self.sock.send(p)
        return True

    def end(self):
        self.sock.close()


class UDPHandler(Handler):
    def open_socket(self, addr, timeout=1.0):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if globalv.communication_simulation:
            timeout = 0.01
        self.sock.settimeout(timeout)

    def get_packet(self, cmd):
        # r = None
        # cnt = 3
        # cnt = 1

        def recv(ds):
            rx, _ = self.sock.recvfrom(ds)
            return rx

        # for _ in range(cnt):
        #     try:
        #         r = self._recvall(recv)
        #         # r, _address = self.sock.recvfrom(self.datasize)
        #         break
        #     except socket.error, e:
        #         self.debug('get_packet {}'.format(e))
        #         self.error_mode = True
        # else:
        #     self.warning('get packet for {} error: {}'.format(cmd, e))
        return self._recvall(recv)

    def send_packet(self, p):
        # self.sock.sendto(p, self.address)
        ok = False
        try:
            self.sock.sendto(p, self.address)
            ok = True
        except (TypeError, socket.error), e:
            self.warning('send packet {} {}'.format(e, self.address))

        return ok


class EthernetCommunicator(Communicator):
    """
    """
    host = None
    port = None
    handler = None
    kind = 'UDP'
    test_cmd = None
    use_end = True
    verbose = False
    error = None
    error_mode = False
    message_frame = ''

    @property
    def address(self):
        return '{}://{}:{}'.format(self.kind, self.host, self.port)

    def load(self, config, path):
        """
        """
        super(EthernetCommunicator, self).load(config, path)

        self.host = self.config_get(config, 'Communications', 'host')
        # self.host = 'localhost'
        self.port = self.config_get(config, 'Communications', 'port', cast='int')

        self.kind = self.config_get(config, 'Communications', 'kind', optional=True)
        self.test_cmd = self.config_get(config, 'Communications', 'test_cmd', optional=True, default='')
        self.use_end = self.config_get(config, 'Communications', 'use_end', cast='boolean', optional=True,
                                       default=False)
        self.message_frame = self.config_get(config, 'Communications', 'message_frame', optional=True, default='')

        if self.kind is None:
            self.kind = 'UDP'

        return True

    def open(self, *args, **kw):

        for k in ('host', 'port', 'message_frame', 'kind'):
            if k in kw:
                setattr(self, k, kw[k])

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
        ret = not self.simulation and handler is not None
        return ret

    def get_handler(self, timeout=1):
        try:
            h = self.handler
            if h is None:
                if self.kind.lower() == 'udp':
                    h = UDPHandler()
                else:
                    h = TCPHandler()

            h.open_socket((self.host, self.port), timeout=timeout)
            h.set_frame(self.message_frame)
            self.handler = h
            return h
        except socket.error, e:
            self.debug(str(e))
            self.error = True
            self.handler = None

    def _reset_connection(self):
        self.handler = None
        self.error = False

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

        if self.error_mode:
            retries = 1

        r = None
        with self._lock:
            re = 'ERROR: Connection refused {}:{}'.format(self.host, self.port)
            for _ in xrange(retries):
                r = self._ask(cmd)
                if r is not None:
                    break
                else:
                    self._reset_connection()

        if r is not None:
            re = self.process_response(r)
        else:
            self.error = True

        if self.use_end:
            handler = self.get_handler()
            handler.end()
            self._reset_connection()

        if verbose or self.verbose and not quiet:
            self.log_response(cmd, re, info)

        return r

    def _ask(self, cmd):
        timeout = 1
        if self.error_mode:
            self.handler = None
            timeout = 0.25

        handler = self.get_handler(timeout)
        # print self.handler, handler, timeout, self.error_mode, cmd
        if not handler:
            self.error_mode = True
            # self.simulation = True
            return
        else:
            self.error_mode = False
            # self.simulation = False

        if handler.send_packet(cmd):
            try:
                return handler.get_packet(cmd)
            except socket.error:
                self.error_mode = True

    def tell(self, cmd, verbose=True, quiet=False, info=None):
        self._lock.acquire()
        handler = self.get_handler()

        if handler.send_packet(cmd):
            if verbose or self.verbose and not quiet:
                self.log_tell(cmd, info)
        self._lock.release()

# ============= EOF ====================================
