# ===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================

#=============standard library imports ========================
import time
import glob
import os
import sys

import serial



#=============local library imports  ==========================
from communicator import Communicator
from pychron.globals import globalv


def get_ports():
    keyspan = glob.glob('/dev/tty.U*')
    usb = glob.glob('/dev/tty.usb*')
    return keyspan + usb


class SerialCommunicator(Communicator):
    '''
        Base Class for devices that communicate using a rs232 serial port.
        Using Keyspan serial converter is the best option for a Mac
        class is built on top of pyserial. Pyserial is used to create a handle and
        this class uses the handle to read and write.
        handles are created when a serial device is opened
        setup args are loaded using load(). this method should be overwritten to
        load specific items.

    '''

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
    clear_output = False


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

    def load(self, config, path):
        '''

        '''

        self.config_path = path
        self.config = config

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
        if parity is not None:
            self.parity = getattr(serial, 'PARITY_%s' % parity.upper())

        stopbits = self.config_get(config, 'Communications', 'stopbits', optional=True)
        if stopbits is not None:
            if stopbits == '1':
                stopbits = 'ONE'
            elif stopbits == '2':
                stopbits = 'TWO'
            self.stopbits = getattr(serial, 'STOPBITS_%s' % stopbits.upper())

        self.set_attribute(config, 'read_delay', 'Communications', 'read_delay',
                           cast='float', optional=True, default=25
        )

        self.set_attribute(config, 'read_terminator', 'Communications', 'terminator',
                           optional=True, default=None)

    def tell(self, cmd, is_hex=False, info=None, verbose=True, **kw):
        '''

        '''
        if self.handle is None:
            if verbose:
                info = 'no handle'
                self.log_tell(cmd, info)
            return

        with self._lock:
        #            self._lock.acquire()
            self._write(cmd, is_hex=is_hex)
            if verbose:
                self.log_tell(cmd, info)

            #        self._lock.release()

            #    def write(self, *args, **kw):
            #        '''
            #        '''
            #        self.info('%s' % args[0], decorate = False)
            #
            #        self._lock.acquire()
            #        self._write(*args, **kw)
            #        self._lock.release()

    def read(self, nchars=None, *args, **kw):
        '''
        '''
        with self._lock:
            if nchars is not None:
            # self._lock.acquire()
                r = self._read_nchars(nchars)
            else:
                r = self._read_terminator(*args, **kw)
                # self._lock.release()
            return r

    def ask(self, cmd, is_hex=False, verbose=True, delay=None,
            replace=None, remove_eol=True, info=None, nbytes=None,
            handshake_only=False,
            handshake=None,
            read_terminator=None,
            nchars=None
    ):
        '''

        '''


        if self.handle is None:
            if verbose:
                self.info('no handle    {}'.format(cmd.strip()))
            return

        if not self.handle.isOpen():
            return 

        with self._lock:
            if self.clear_output:
                self.handle.flushInput()
                self.handle.flushOutput()
            #            self.info('acquiring lock {}'.format(self._lock))
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
                # print read_terminator
                re = self._read_terminator(delay=delay,
                                           terminator=read_terminator)
        if remove_eol:
            re = self._remove_eol(re)

        # print re, len(re)
        if verbose:
            # self.debug('lock acquired by {}'.format(currentThread().name))
            pre = self.process_response(re, replace)
            self.log_response(cmd, pre, info)
            # self.debug('lock released by {}'.format(currentThread().name))

        #            time.sleep(0.005)
        #            self.info('release lock {}'.format(self._lock))
        return re

    def open(self, **kw):
        '''
            Use pyserial to create a handle connected to port wth baudrate
            default handle parameters
            baudrate=9600
            bytesize=EIGHTBITS
            parity= PARITY_NONE
            stopbits= STOPBITS_ONE
            timeout=None
        '''
        args = dict()

        ldict = locals()['kw']
        port = ldict['port'] if 'port' in ldict else None

        if port is None:
            port = self.port
            if port is None:
                self.warning('Port not set')
                return False

        #=======================================================================
        # #on windows device handles probably handled differently
        if sys.platform == 'darwin':
            port = '/dev/tty.{}'.format(port)
            #=======================================================================

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

                self.config.set('Communication', 'port', )
                self.write_configuration(self.config, self.config_path)

            self.handle = None
            self.simulation = True

    def _validate_address(self, port):
        '''
            use glob to check the avaibable serial ports
            valid ports start with /dev/tty.U or /dev/tty.usbmodem

        '''
        valid = get_ports()
        if port in valid:
            return True
        else:
            msg = '{} is not a valid port address'.format(port)
            self.warning(msg)
            if not valid:
                wmsg = 'No valid ports'
                self.warning(wmsg)
            else:
                for v in valid:
                    self.warning(v)

                wmsg = '\n'.join(valid)

            if not globalv.ignore_connection_warnings:
                if self.confirmation_dialog('{}\n{}\n\nQuit Pychron?'.format(msg, wmsg),
                                            title='Quit Pychron'):
                    os._exit(0)

                #            valid = '\n'.join(['%s' % v for v in valid])
                #            self.warning('''%s is not a valid port address
                #==== valid port addresses ==== \n%s''' % (port, valid))


    def _write(self, cmd, is_hex=False):
        '''
            use the serial handle to write the cmd to the serial buffer

        '''

        def write(cmd_str):
            try:
                # print 'cmd', cmd_str, len(cmd_str)
                self.handle.write(cmd_str)
            except (serial.serialutil.SerialException, OSError, IOError, ValueError), e:
                self.warning(e)

        if not self.simulation:

            if is_hex:
                cmd = cmd.decode('hex')
                # write(cmd)
            else:
                if self.write_terminator is not None:
                    cmd += self.write_terminator

                #                if self.char_write:
                #                    for c in cmd:
                #                        write(c)
                #                        time.sleep(0.0005)
                #                else:
                #                    write(cmd)
                #            time.sleep(50e-9)
            write(cmd)

    def _read_nchars(self, n, timeout=1, delay=None):
        func = lambda r: self._get_nchars(n, r)
        return self._read_loop(func, delay, timeout)

    def _read_hex(self, nbytes=8, timeout=1, delay=None):
    #        print nbytes
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

    #        r=self._read_loop(hfunc, delay, timeout)
    #        r=

    def _read_terminator(self, timeout=1, delay=None,
                         terminator=None):
    #        func = (lambda: self._get_nbytes(nbytes)) \
    #                if is_hex else lambda: self._get_isterminated(self.read_terminator)
        if terminator is None:
            terminator = self.read_terminator

        func = lambda r: self._get_isterminated(r, terminator)
        return self._read_loop(func, delay, timeout)

    #        if delay is not None:
    #            time.sleep(delay / 1000.)
    #
    #        elif self.read_delay:
    #            time.sleep(self.read_delay / 1000.)
    #
    #        r = None
    #        st = time.time()
    #
    #        while time.time() - st < timeout:
    #            if handshake is not None:
    #                ack, r = self._check_handshake(handshake)
    #                if handshake_only and ack:
    #                    r = handshake[0]
    #                    break
    #                elif ack and r is not None:
    #                    break
    #            else:
    #                try:
    #                    r, isline = func()
    #                    if isline:
    #                        break
    #                except (ValueError, TypeError):
    #                    import traceback
    #                    traceback.print_exc()
    #                time.sleep(0.001)

    #        return r

    def _get_nbytes(self, nchars, r):
        '''
            1 byte == 2 chars
        '''
        handle = self.handle
        #        inw = 0
        #        timeout = 1
        #        tt = 0
        #        r = ''

        #        while len(r) < nbytes and tt < timeout:
        inw = handle.inWaiting()
        #            c = inw
        c = min(inw, nchars - len(r))
        r += ''.join(map('{:02X}'.format, map(ord, handle.read(c))))
        #        print len(r), nchars
        #            d = 1 / 1000.
        #            time.sleep(d)
        #            tt += d
        #        print len(r), nchars
        return r[:nchars], len(r) >= nchars

    def _get_nchars(self, nchars, r):
        '''
        '''
        handle = self.handle
        inw = handle.inWaiting()
        c = min(inw, nchars - len(r))
        r += handle.read(c)
        # print 'get n', len(r), nchars, self._prep_str(r), len(r) == nchars
        return r[:nchars], len(r) >= nchars

    def _check_handshake(self, handshake_chrs):
        ack, nak = handshake_chrs
        inw = self.handle.inWaiting()
        r = self.handle.read(inw)
        if r:
            return ack == r[0], r[1:]
        return False, None

    def _get_isterminated(self, r, terminator=None):
        terminated = False
        try:
            inw = self.handle.inWaiting()
            r += self.handle.read(inw)
            #            print 'inw', inw, r, terminator
            if terminator is None:
                terminator = ('\n', '\r')

            if not isinstance(terminator, (list, tuple)):
                terminator = (terminator,)

            if r and r.strip():
                for ti in terminator:
                #                    print ' '.join(map(str,[ord(t) for t in ti])),' '.join(map(str,[ord(t) for t in r]))
                    if r.endswith(ti):
                        terminated = True
                        break
                    #                terminated = r[-1] in terminator

                    #                t1 = '\n'
                    #                t2 = '\r'
                    #                return r, r.endswith(t1) or r.endswith(t2) if r is not None else False
                    #            else:
                    #                return r, r.endswith(terminator) if r is not None else False

        except (OSError, IOError), e:
            self.warning(e)
        return r, terminated

    def _read_loop(self, func, delay, timeout=1):
        # print func, delay, timeout
        if delay is not None:
            time.sleep(delay / 1000.)

        elif self.read_delay:
            time.sleep(self.read_delay / 1000.)

        r = ''
        st = time.time()

        handle=self.handle

        ct = time.time()
        while ct - st < timeout:
            if not handle.isOpen():
                break
            
            try:
                r, isterminated = func(r)
                #                print r, isterminated
                if isterminated:
                    break
            except (ValueError, TypeError):
                pass
#                import traceback
#                traceback.print_exc()
            time.sleep(0.01)
            ct = time.time()

        if ct - st > timeout:
            l = len(r) if r else 0
            self.info('timed out. {}s r={}, len={}'.format(timeout, r, l))

        return r

    #    def _read(self, is_hex=False, time_out=1, delay=None):
#        '''
#            use the serial handle to read available bytes from the serial buffer
#
#        '''
#        def err_handle(func):
#            def _err(*args):
#                try:
#                    return func(*args)
#                except (OSError, IOError), e:
#                    self.warning(e)
#            return _err
#
# #        @err_handle
# #        def eread(inw):
# #            return self.handle.read(inw)
# #            r = None
# #            try:
# #                r = self.handle.read(inw)
# #            except (OSError, IOError), e:
# #                self.warning(e)
# #            return r
#
# #        @err_handle
# #        def get_chars():
# #            return self.handle.inWaiting()
# #            c = 0
# #            try:
# #                c = self.handle.inWaiting()
# #            except (OSError, IOError), e:
# #                self.warning(e)
# #            return c
#
#        def get_line(terminator=None):
#            try:
#                inw = self.handle.inWaiting()
#                r = self.handle.read(inw)
#                if terminator is None:
#                    t1 = '\n'
#                    t2 = '\r'
#                    isline = r.endswith(t1) or r.endswith(t2) if r is not None else False
#                else:
#                    isline = r.endswith(terminator) if r is not None else False
#            except (OSError, IOError), e:
#                self.warning(e)
# ##            print isline, r, inw
#            return isline, r, inw
#
#        r = None
#        if self.simulation:
#            r = 'simulation'
#        else:
#            if delay is None:
#                delay = self.read_delay
#
#            if delay:
#                time.sleep(delay / 1000.)
#
#            time.sleep(self.read_delay)
#            ready_to_read, _, _ = select.select([self.handle], [], [], 0.5)
#            if ready_to_read:
#                isline, r, c = get_line(terminator=self.read_terminator)
#                if is_hex:
#                    if r:
#                        r = ''.join(['{:02X}'.format(ri) for ri in map(ord, r)])
#                elif not isline:
#                    pcnt = 0
#                    cnt = 0
#                    for _ in xrange(200000):
#                        isline, r, c = get_line(terminator=self.read_terminator)
#                        if isline:
#                            break
#                        if pcnt == c:
#                            cnt += 1
#                        else:
#                            cnt = 0
#
#                        pcnt = c
#                        if cnt > 50000:
#                            break
#
# #                    print 'line', c
#
#
#        return r
# #            if inw > 0:
# #                try:
# #                    r = self.handle.read(inw)
# ##                    self.handle.flush()
# #                    if is_hex:
# #                        r = ''.join(['{:02X}'.format(ri) for ri in map(ord, r)])
# ##                        rr = ''
# ##                        for ri in r:
# ##                            rr += '{:02X}' % ord(ri)
# ##                        r = rr
# #
# #                except (OSError, IOError), e:
# #                    self.warning(e)
#
# #        else:
# #            r = 'simulation'
# #
# #        return r

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
#===================== EOF ==========================================
