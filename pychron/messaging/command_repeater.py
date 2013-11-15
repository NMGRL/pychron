#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Button, Instance, String, Property
from traitsui.api import View, HGroup, Item, Handler
#============= standard library imports ========================
import socket
import os
from random import random
from threading import Lock
#============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
from pychron.remote_hardware.errors import PychronCommErrorCode
from pychron.globals import globalv
from pychron.ui.led_editor import LED, LEDEditor


class CRHandler(Handler):
    def init(self, info):
        '''
  
        '''
        info.object.test_connection()


class CommandRepeater(ConfigLoadable):
    '''
    '''
    path = String(enter_set=True, auto_set=False)
    target_name = Property(depends_on='path')
    test = Button
    led = Instance(LED, ())

    def _get_target_name(self):
        ta = os.path.basename(self.path)
        ta = ta.replace('hardware-', '')
        return ta

    def load(self, *args, **kw):
        '''
        '''
        config = self.get_configuration()

        if config:
            self.path = self.config_get(config, 'Repeater', 'path')
            self.info('configured for {}'.format(self.path))
            return True

    def open(self, *args, **kw):

        kind = socket.SOCK_STREAM
        if globalv.ipc_dgram:
            kind = socket.SOCK_DGRAM

        sock = socket.socket(socket.AF_UNIX, kind)

        sock.settimeout(2)
        self._sock = sock

        # create a sync lock
        self._lock = Lock()

        return True

    def get_response(self, rid, data, sender_address, verbose=True):
        '''
        '''
        # intercept the pychron ready command
        # sent a test query
        with self._lock:
            ready_flag = False
            ready_data = ''
            if data == 'PychronReady':
                ready_flag = True
                ready_data = '{:0.3f}'.format(random())
                rid = 'test'

            elif data == 'RemoteLaunch':
                return self.remote_launch('pychron')

            try:
                self._sock.connect(self.path)
            except socket.error:
                # _sock is already connected
                pass

            s = '{}|{}|{}'.format(rid, data, sender_address)

            send_success, rd = self._send_(s, verbose=verbose)
            if send_success:
                read_success, rd = self._read_(verbose=verbose)
                if read_success:
                    self.led.state = 'green'

            if send_success and read_success:
                if ready_flag and ready_data == rd:
                    rd = 'OK'

                result = rd.split('|')[1] if '|' in rd else rd

            else:
                self.led.state = 'red'
                result = str(PychronCommErrorCode(self.path, rd))

            if ready_flag and data == result:
                result = 'OK'

            return result

#===============================================================================
# commands
#===============================================================================
    def test_connection(self, verbose=True):
        '''
        '''
        ra = '{:0.3f}'.format(random())

        r = self.get_response('test', ra, None, verbose=verbose)
        connected = False
        if 'ERROR 6' in r:
            self.led.state = 'red'
        elif r == ra:
            self.led.state = 'green'
            connected = True

        if verbose:
            self.debug('Connection State - {}'.format(connected))
        return connected

    def remote_launch(self, name):
        import subprocess
        from os import path
        from pychron.paths import paths

        # launch pychron
        p = path.join(paths.pychron_src_root, '{}.app'.format(name))
        result = 'OK'
        try:
            subprocess.Popen(['open', p])
        except OSError:
            result = 'ERROR: failed to launch Pychron'

        return result

#===============================================================================
# response helpers
#===============================================================================
    def _send_(self, s, verbose=True):
        success = True
        e = None
        try:
            totalsent = 0
            mlen = len(s)
            s = '{:02X}{}'.format(mlen, s)

            while totalsent < mlen:
                sent = self._sock.send(s[totalsent:])
                totalsent += sent

        except socket.error, e:
            success = self._handle_socket_send_error(e, s, verbose)

        return success, e

    def _read_(self, count=0, verbose=True):
        rd = None
        try:
            rd = self._sock.recv(2048)
            success = True
        except socket.error, e:
            success, rd = self._handle_socket_read_error(e, count, verbose)

        return success, rd

    def _handle_socket_send_error(self, e, s, verbose):
        retries = 0

        for ei in ['Errno 32', 'Errno 9', 'Errno 11']:
            if ei in str(e):
                retries = 3
                break

        if verbose:
            self.info('send failed - {} - retrying n={}'.format(e, retries))

        # use a retry loop only if error is a broken pipe
        for i in range(retries):
            try:
                self.open()
                try:
                    self._sock.connect(self.path)
                except socket.error, e:
                    if verbose:
                        self.debug('connecting to {} failed. {}'.
                                   format(self.path, e))

                self._send_(s, verbose)
#                self._sock.send(s)
                if verbose:
                    self.debug('send success on retry {}'.format(i + 1))
                return True

            except socket.error, e:
                if verbose:
                    self.debug('send retry {} failed. {}'.format(i + 1, e))

        if verbose:
            self.info('send failed after {} retries. {}'.format(retries, e))

    def _handle_socket_read_error(self, e, count, verbose):
        if verbose:
            self.debug('read error {}'.format(e))
        if 'timed out' in e and count < 3:
            if verbose:
                self.debug('read timed out. doing recursive retry')
            return self._read_(count=count + 1)

        return False, e

#==============================================================================
# View
#==============================================================================
    def _path_changed(self, old, new):
        '''
        '''
        if old:
            self.info('reconfigured for {}'.format(self.path))

    def _test_fired(self):
        '''
        '''
        self.test_connection()

    def simple_view(self):
        v = View(
                 HGroup(
                        Item('led', editor=LEDEditor(), show_label=False),
                        Item('target_name',
                             style='readonly',
                             width=100,
                             show_label=False),
                        ),
                 )
        return v
    def traits_view(self):
        '''
        '''
        v = View(
                 'path',
                    HGroup(
                           Item('led', editor=LEDEditor(), show_label=False),
                           Item('test', show_label=False),

                           ),
                    handler=CRHandler,
                    )
        return v


def profiling():
    import profile

    repeator = CommandRepeater(configuration_dir_name='servers',
                               name='repeater')
#    repeator.load()
    repeator.bootstrap()
#    repeator.test_connection()

    profile.runctx('repeator.get_response(*args)', globals(), {'repeator':repeator, 'args':(1, 2, 3) })

if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    logging_setup('profile_repeator')
    profiling()
#============= EOF ====================================

#===============================================================================
# SHMCommandRepeater
#===============================================================================

# class SHMCommandRepeater(SHMClient):
#    '''
#    '''
#    path = String(enter_set=True, auto_set=False)
#
#    test = Button
#    led = Instance(LED, ())
#    def _test_fired(self):
#        '''
#        '''
#        self.test_connection()
#
#    def test_connection(self):
#        '''
#        '''
#        ra = '%0.3f' % random.random()
#        r = self.get_response('test', ra)
#
#        if r is None:
#            self.led.state = 0
#        elif r == ra:
#            self.led.state = 2
#
#    def _path_changed(self, old, new):
#        '''
#        '''
#        if old:
#            self.info('reconfigured for %s' % self.path)
#
#    def traits_view(self):
#        '''
#        '''
#        v = View(
#                 'path',
#                    HGroup(
#                           Item('led', editor=LEDEditor(), show_label=False),
#                           Item('test', show_label=False),
#
#                           ),
#                    handler=CRHandler,
#                    )
#        return v
#
#    def load(self, *args, **kw):
#        '''
#
#        '''
#
#        config = self.get_configuration()
#
#        if config:
#            self.path = self.config_get(config, 'General', 'path')
#            self.info('configured for %s' % self.path)
#            return True
#
#    def get_response(self, _type, data):
#        '''
#
#        '''
#
#        return self.send_command('|'.join((_type, data)))
