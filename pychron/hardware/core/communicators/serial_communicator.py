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
# =============enthought library imports=======================

# =============standard library imports ========================
import time
import glob
import os
import sys

import serial


# =============local library imports  ==========================
from communicator import Communicator, process_response, prep_str, remove_eol_func
from pychron.globals import globalv


def get_ports():
    usb = glob.glob('/dev/tty.usb*')
    if sys.platform == 'darwin':
        keyspan = glob.glob('/dev/tty.U*')
    else:
        keyspan = glob.glob('/dev/ttyU*')

    return keyspan + usb


class SerialCommunicator(Communicator):
    """
        Base Class for devices that communicate using a rs232 serial port.
        Using Keyspan serial converter is the best option for a Mac
        class is built on top of pyserial. Pyserial is used to create a handle and
        this class uses the handle to read and write.
        handles are created when a serial device is opened
        setup args are loaded using load(). this method should be overwritten to
        load specific items.

    """

    # char_write = False

    _auto_find_handle = False
    _auto_write_handle = False
    baudrate = None
    port = None
    bytesize = None
    parity = None
    stopbits = None
    timeout = None

    id_query = ''
    id_response = ''

    read_delay = None
    read_terminator = None
    read_terminator_position = None
    clear_output = False

    _config = None

    @property
    def address(self):
        return self.port

    def test_connection(self):
        return self.handle is not None

    def reset(self):
        handle = self.handle
        try:
            isopen = handle.isOpen()
            orate = handle.getBaudrate()
            if isopen:
                handle.close()

            handle.setBaudrate(0)
            handle.open()
            time.sleep(0.1)
            handle.close()

            handle.setBaudrate(orate)
            if isopen:
                handle.open()

        except Exception:
            self.warning('failed to reset connection')

    def close(self):
        if self.handle:
            self.debug('closing handle {}'.format(self.handle))
            self.handle.close()

    def load_comdict(self, port, baudrate=9600, bytesize=8, parity=None, stopbits=1):
        self.baudrate = baudrate
        self.port = port
        self.set_parity(parity)
        self.set_stopbits(stopbits)
        self.bytesize = bytesize

    def load(self, config, path):

        self.config_path = path
        self._config = config

        self.set_attribute(config, 'port', 'Communications', 'port')
        self.set_attribute(config, 'baudrate', 'Communications', 'baudrate',
                           cast='int', optional=True)
        self.set_attribute(config, 'bytesize', 'Communications', 'bytesize',
                           cast='int', optional=True)
        self.set_attribute(config, 'timeout', 'Communications', 'timeout',
                           cast='float', optional=True)

        self.set_attribute(config, 'clear_output', 'Communications', 'clear_output',
                           cast='boolean', optional=True)

        parity = self.config_get(config, 'Communications', 'parity', optional=True)
        self.set_parity(parity)

        stopbits = self.config_get(config, 'Communications', 'stopbits', optional=True)
        self.set_stopbits(stopbits)

        self.set_attribute(config, 'read_delay', 'Communications', 'read_delay',
                           cast='float', optional=True, default=25)

        self.set_attribute(config, 'read_terminator', 'Communications', 'terminator',
                           optional=True, default=None)

        self.set_attribute(config, 'read_terminator_position', 'Communications', 'terminator_position',
                           optional=True, default=None, cast='int')

        if self.read_terminator == 'ETX':
            self.read_terminator = chr(3)

    def set_parity(self, parity):
        if parity is not None:
            self.parity = getattr(serial, 'PARITY_%s' % parity.upper())

    def set_stopbits(self, stopbits):
        if stopbits is not None:
            if stopbits in ('1', 1):
                stopbits = 'ONE'
            elif stopbits in ('2', 2):
                stopbits = 'TWO'
            self.stopbits = getattr(serial, 'STOPBITS_{}'.format(stopbits.upper()))

    def tell(self, cmd, is_hex=False, info=None, verbose=True, **kw):
        """
        """
        if self.handle is None:
            if verbose:
                info = 'no handle'
                self.log_tell(cmd, info)
            return

        with self._lock:
            self._write(cmd, is_hex=is_hex)
            if verbose:
                self.log_tell(cmd, info)

    def read(self, nchars=None, *args, **kw):
        """
        """
        with self._lock:
            if nchars is not None:
                r = self._read_nchars(nchars)
            else:
                r = self._read_terminator(*args, **kw)

            return r

    def ask(self, cmd, is_hex=False, verbose=True, delay=None,
            replace=None, remove_eol=True, info=None, nbytes=None,
            handshake_only=False,
            handshake=None,
            read_terminator=None,
            nchars=None):
        """
        """

        if self.handle is None:
            if verbose:
                x = prep_str(cmd.strip())
                self.info('no handle    {}'.format(x))
            return

        if not self.handle.isOpen():
            return

        with self._lock:
            if self.clear_output:
                self.handle.flushInput()
                self.handle.flushOutput()
            self._write(cmd, is_hex=is_hex)
            if is_hex:
                if nbytes is None:
                    nbytes = 8
                re = self._read_hex(nbytes=nbytes, delay=delay)
            elif handshake is not None:
                re = self._read_handshake(handshake, handshake_only, delay=delay)
            elif nchars is not None:
                re = self._read_nchars(nchars)
            else:
                re = self._read_terminator(delay=delay,
                                           terminator=read_terminator)
        if remove_eol:
            re = remove_eol_func(re)

        if verbose:
            pre = process_response(re, replace)
            self.log_response(cmd, pre, info)

        return re

    def open(self, **kw):
        """
            Use pyserial to create a handle connected to port wth baudrate
            default handle parameters
            baudrate=9600
            bytesize=EIGHTBITS
            parity= PARITY_NONE
            stopbits= STOPBITS_ONE
            timeout=None
        """
        args = dict()

        ldict = locals()['kw']
        port = ldict['port'] if 'port' in ldict else None

        if port is None:
            port = self.port
            if port is None:
                self.warning('Port not set')
                return False

        # #on windows device handles probably handled differently
        if sys.platform == 'darwin':
            port = '/dev/tty.{}'.format(port)

        args['port'] = port

        for key in ['baudrate', 'bytesize', 'parity', 'stopbits', 'timeout']:
            v = ldict[key] if key in ldict else None
            if v is None:
                v = getattr(self, key)
            if v is not None:
                args[key] = v

        pref = kw['prefs'] if 'prefs' in kw else None
        if pref is not None:
            pref = pref.serial_preference
            self._auto_find_handle = pref.auto_find_handle
            self._auto_write_handle = pref.auto_write_handle

        self.simulation = True
        if self._validate_address(port):
            try_connect = True
            while try_connect:
                try:
                    self.handle = serial.Serial(**args)
                    try_connect = False
                    self.simulation = False

                except serial.serialutil.SerialException:
                    try_connect = False
        elif self._auto_find_handle:
            self._find_handle(args, **kw)

        connected = True if self.handle is not None else False
        return connected

    # private
    def _find_handle(self, args, **kw):
        found = False
        self.simulation = False
        self.info('Trying to find correct port')

        port = None
        for port in get_ports():
            self.info('trying port {}'.format(port))
            args['port'] = port
            try:
                self.handle = serial.Serial(**args)
            except serial.SerialException:
                continue

            r = self.ask(self.id_query)

            # use id_response as a callable to do device specific
            # checking
            if callable(self.id_response):
                if self.id_response(r):
                    found = True
                    self.simulation = False
                    break

            if r == self.id_response:
                found = True
                self.simulation = False
                break

        if not found:

            # update the port
            if self._auto_write_handle and port:
                # port in form
                # /dev/tty.USAXXX1.1
                p = os.path.split(port)[-1]
                # remove tty.
                p = p[4:]

                self._config.set('Communication', 'port', )
                self.write_configuration(self._config, self.config_path)

            self.handle = None
            self.simulation = True

    def _validate_address(self, port):
        """
            use glob to check the avaibable serial ports
            valid ports start with /dev/tty.U or /dev/tty.usbmodem

        """
        valid = get_ports()
        if port in valid:
            return True
        else:
            msg = '{} is not a valid port address'.format(port)
            self.warning(msg)
            if not valid:
                self.warning('No valid ports')
            else:
                self.warning('======== Valid Ports ========')
                for v in valid:
                    self.warning(v)
                self.warning('=============================')

                # wmsg = '\n'.join(valid)
            # if not globalv.ignore_connection_warnings:
            #
            #     if self.confirmation_dialog('{}\n{}\n\nQuit Pychron?'.format(msg, wmsg),
            #                                 title='Quit Pychron'):
            #         os._exit(0)

    def _write(self, cmd, is_hex=False):
        """
            use the serial handle to write the cmd to the serial buffer

        """

        def write(cmd_str):
            try:
                self.handle.write(cmd_str)
            except (serial.serialutil.SerialException, OSError, IOError, ValueError), e:
                self.warning(e)

        if not self.simulation:

            if is_hex:
                cmd = cmd.decode('hex')
            else:
                if self.write_terminator is not None:
                    cmd += self.write_terminator

            write(cmd)

    def _read_nchars(self, n, timeout=1, delay=None):
        func = lambda r: self._get_nchars(n, r)
        return self._read_loop(func, delay, timeout)

    def _read_hex(self, nbytes=8, timeout=1, delay=None):
        func = lambda r: self._get_nbytes(nbytes * 2, r)
        return self._read_loop(func, delay, timeout)

    def _read_handshake(self, handshake, handshake_only, timeout=1, delay=None):
        def hfunc(r):
            terminated = False
            ack, r = self._check_handshake(handshake)
            if handshake_only and ack:
                r = handshake[0]
                terminated = True
            elif ack and r is not None:
                terminated = True
            return r, terminated

        return self._read_loop(hfunc, delay, timeout)

    def _read_terminator(self, timeout=1, delay=None,
                         terminator=None):

        if terminator is None:
            terminator = self.read_terminator

        pos = self.read_terminator_position

        def func(r):
            return self._get_isterminated(r, terminator, pos)

        return self._read_loop(func, delay, timeout)

    def _get_nbytes(self, nchars, r):
        """
            1 byte == 2 chars
        """
        handle = self.handle
        inw = handle.inWaiting()
        c = min(inw, nchars - len(r))
        r += ''.join(map('{:02X}'.format, map(ord, handle.read(c))))

        return r[:nchars], len(r) >= nchars

    def _get_nchars(self, nchars, r):
        handle = self.handle
        inw = handle.inWaiting()
        c = min(inw, nchars - len(r))
        r += handle.read(c)
        return r[:nchars], len(r) >= nchars

    def _check_handshake(self, handshake_chrs):
        ack, nak = handshake_chrs
        inw = self.handle.inWaiting()
        r = self.handle.read(inw)
        if r:
            return ack == r[0], r[1:]
        return False, None

    def _get_isterminated(self, r, terminator=None, pos=None):
        terminated = False
        try:
            inw = self.handle.inWaiting()
            r += self.handle.read(inw)
            #            print 'inw', inw, r, terminator
            if terminator is None:
                terminator = ('\n', '\r', '\r\x00')
            if not isinstance(terminator, (list, tuple)):
                terminator = (terminator,)

            if r and r.strip():
                for ti in terminator:
                    if pos:
                        t = r[pos] == ti
                    else:
                        t = r.endswith(ti)

                    if t:
                        terminated = True
                        break
        except BaseException, e:
            self.warning(e)
        return r, terminated

    def _read_loop(self, func, delay, timeout=1):
        if delay is not None:
            time.sleep(delay / 1000.)

        elif self.read_delay:
            time.sleep(self.read_delay / 1000.)

        r = ''
        st = time.time()

        handle = self.handle

        ct = time.time()
        while ct - st < timeout:
            if not handle.isOpen():
                break

            try:
                r, isterminated = func(r)
                if isterminated:
                    break
            except (ValueError, TypeError):
                pass
            time.sleep(0.01)
            ct = time.time()

        if ct - st > timeout:
            l = len(r) if r else 0
            self.info('timed out. {}s r={}, len={}'.format(timeout, r, l))

        return r


if __name__ == '__main__':
    s = SerialCommunicator()
    s.read_delay = 0
    s.port = 'usbmodemfd1221'
    s.open()
    time.sleep(2)
    s.tell('A', verbose=False)

    for i in range(10):
        print 'dddd', s.ask('1', verbose=False)
        time.sleep(1)
#    s.tell('ddd', verbose=False)
#    print s.ask('ddd', verbose=False)
# ===================== EOF ==========================================
