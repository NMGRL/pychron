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

#============= enthought library imports =======================
from traits.api import Bool, Str
#============= standard library imports ========================
import socket
from threading import Thread, Lock
import os
import select
#============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
from pychron.remote_hardware.errors.error import ErrorCode
from pychron.remote_hardware.context import ContextFilter
from pychron.remote_hardware.errors import SystemLockErrorCode, \
    SecurityErrorCode
from pychron.globals import globalv
BUFSIZE = 2048

def end_request(fn):
    def end(obj, rtype, data, sender, sock=None):
        data = fn(obj, rtype, data, sender)
        if isinstance(data, ErrorCode):
            data = str(data)

        if globalv.use_ipc:
            # self.debug('Result: {}'.format(data))
#            if isinstance(data, ErrorCode):
#                data = str(data)
            try:
                if globalv.ipc_dgram:
                    sock.sendto(data, obj.path)
                else:
                    sock.send(str(data))
                # sock.close()
            except Exception, err:
                obj.debug('End Request Exception: {}'.format(err))
        else:
            return data
#            if not isinstance(data, ErrorCode) and data:
#                data = data.split('|')[-1]
#            else:
#                print data
#            return str(data)

    return end


# def memoize_value(func):
#    stored = []
#    def memoized():
#        try:
#            return stored[0]
#        except IndexError:
#            result = func()
#            stored.append(result)
#            return result
#
#    return memoized
#
# @memoize_value
# def get_authentication_hmac():
#    '''
#        only open an read the file on start up
#        memoize_value stores the result
#    '''
#    from pychron.core.helpers.paths import setup_dir
#    p = os.path.join(setup_dir, 'hmac')
#    #read a config file
#    with open(p, 'r') as f:
#        return hmac.new(f.read()).digest()


class CommandProcessor(ConfigLoadable):
    '''
    listens to a specified port for incoming requests.
    request will come from the repeater
    '''
    # port = None
    path = None

    _listen = True
    simulation = False
    manager = None
    _sock = None

    system_lock_name = Str
    system_lock = Bool(False)
    system_lock_address = Str

    _handlers = None
    _manager_lock = None

    use_security = False
    _hosts = None

    def __init__(self, *args, **kw):
        super(CommandProcessor, self).__init__(*args, **kw)
        self.context_filter = ContextFilter()
        self._handlers = dict()
        self._manager_lock = Lock()
        self._hosts = []

    def get_response(self, rtype, data, sender):
        return self._process_request(rtype, data, sender)

    def close(self):
        """
        """
        if not globalv.use_ipc:
            return

        self.info('Stop listening to {}'.format(self.path))
        self._listen = False
        if self._sock:
            self._sock.close()

    def open(self, *args, **kw):
        """
        """
        if not globalv.use_ipc:
            return True

        kind = socket.SOCK_STREAM
        if globalv.ipc_dgram:
            kind = socket.SOCK_DGRAM

        self._sock = socket.socket(socket.AF_UNIX, kind)
        # self._sock.settimeout(1)
        if not globalv.ipc_dgram:
            self._sock.setblocking(False)

        try:
            os.unlink(self.path)
        except OSError:
            pass

        self._sock.bind(self.path)

        if not globalv.ipc_dgram:
            self._sock.listen(10)

        self.info('listening to {} using {}'.format(self.path,
                        'DATAGRAM' if globalv.ipc_dgram else 'STREAM'))

        t = Thread(name='processor.listener',
                   target=self._listener)
        t.setDaemon(1)
        t.start()

        return True

    def _listener(self, *args, **kw):
        """
        """
        _input = [self._sock]
        while self._listen:
            try:
                if globalv.ipc_dgram:
                    self._dgram_listener()
                else:
                    self._stream_listener(_input)

            except Exception, err:
                self.debug('Listener Exception {}'.format(err))
                import traceback
                tb = traceback.format_exc()
                self.debug(tb)

    def _stream_listener(self, isock):
        try:
            ins, _, _ = select.select(isock, [], [], 5)

            for s in ins:
                if s == self._sock:
                    client, _addr = self._sock.accept()
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

    def _dgram_listener(self):
        print 'daga'
        try:
            data, address = self._sock.recv(BUFSIZE)
            print data, address, 'f'
            if data is not None:
                self._process_data(self._sock, data)
        except socket.error:
            pass
#            args = [self._sock] + data.split('|')
#            if len(args) == 4:
# #            if self._threaded:
# #                t = Thread(target=self._process_request, args=args)
# #                t.start()
# #            else:
#                self._process_request(*args)

    def _read(self, sock):
        data = sock.recv(BUFSIZE)
        if data:
            mlen = int(data[:4], 16)
            while len(data) < (mlen + 4):
                data += sock.recv(BUFSIZE)

            return data[4:]

    def _process(self, sock, data):
        args = data.split('|')
        try:
            request_type, data, sender_addr = args
        except ValueError, e:
            self.debug('data = {}'.format(data))
            self.debug('too many args {}, {}'.format(len(args), args))
            try:
                request_type, data, sender_addr = args[-3:]
            except ValueError:
                return

        resp = self._process_request(request_type, data, sender_addr)
        if resp:
            self._end_request(sock, resp)

    def _process_request(self, request_type, data, sender_addr):
        # self.debug('Request: {}, {}'.format(request_type, data.strip()))
        try:

            auth_err = self._authenticate(data, sender_addr)
            if auth_err:
                return auth_err

            if not request_type in ['Extractionline',
                                    'Diode',
                                    'Synrad',
                                    'CO2',
                                    'UV',
                                    'Hardware',
                                    'test']:
                self.warning('Invalid request type ' + request_type)
                return

            if request_type == 'test':
                return data

            handler = None
            klass = '{}Handler'.format(request_type.capitalize())
            if klass not in self._handlers:
                pkg = 'pychron.remote_hardware.handlers.{}_handler'.format(request_type.lower())
                try:
                    module = __import__(pkg, globals(), locals(), [klass])
                    factory = getattr(module, klass)
                    handler = factory(application=self.application)
                    self._handlers[klass] = handler
                    '''
                        the context filter uses the handler object to
                        get the kind and request
                        if the min period has elapse since last request or the message is triggered
                        get and return the state from pychron

                        pure frequency filtering could be accomplished earlier in the stream in the 
                        Remote Hardware Server (CommandRepeater.get_response) 
                    '''
                except ImportError, e:
                    return 'ImportError klass={} pkg={} error={}'.format(klass, pkg, e)
            else:
                handler = self._handlers[klass]

            if handler is not None:
                return handler.handle(data, sender_addr, self._manager_lock)

        except Exception, err:
            import traceback

            tb = traceback.format_exc()
            self.debug(tb)

            self.debug('Process request Exception {}'.format(err))
            traceback.print_exc()

    def _end_request(self, sock, data):
        if isinstance(data, ErrorCode):
            data = str(data)

        n = len(data) + 4
        data = '{:04X}{}'.format(n, data)
        #self.debug('response len={}'.format(n))
        if globalv.use_ipc:
            try:
                if globalv.ipc_dgram:
                    func = lambda x: sock.sendto(x, self.path)
                else:
                    func = lambda x: sock.send(x)

                mlen = len(data)
                totalsent = 0
                while totalsent < mlen:
                    try:
                        totalsent += func(data[totalsent:])
                        #self.debug('totalsent={} n={}'.format(totalsent, mlen))
                    except socket.error:
                        continue

            except Exception, err:
                self.debug('End Request Exception: {}'.format(err))
        else:
            return data

    def _check_system_lock(self, addr):
        '''
            return true if addr is not equal to the system lock address
            ie this isnt who locked us so we deny access
        '''
        if self.system_lock:
            if not addr in [None, 'None']:
                return self.system_lock_address != addr

    def _authenticate(self, data, sender_addr):
        if self.use_security:
            # check sender addr is in hosts
            if self._hosts:
                if not sender_addr in self._hosts:
                    for h in self._hosts:
                        # match to any computer on the subnet
                        hargs = h.split('.')
                        if hargs[-1] == '*':
                            if sender_addr.split('.')[:-1] == hargs[:-1]:
                                break
                    else:
                        return str(SecurityErrorCode(sender_addr))
            else:
                self.warning('hosts not configured, security not enabled')

        if self._check_system_lock(sender_addr):
            return str(SystemLockErrorCode(self.system_lock_name,
                                         self.system_lock_address,
                                         sender_addr, logger=self.logger))
# if __name__ == '__main__':
#    setup('command server')
#    e = CommandProcessor(name='command_server',
#                                  configuration_dir_name='servers')
#    e.bootstrap()
#============= EOF ====================================
#
#    def _handler(self, rsock):
#        '''
#        '''
#        data = rsock.recv(1024)
#        #self.debug('Received %s' % data)
# #        if self.manager is not None:
#        ptype, payload = data.split('|')
#
# #            t = Thread(target=self.manager.process_server_request, args=(ptype, payload))
# #            t.start()
# #            t.join()
#
#            #response = self.manager.get_server_response()
#
#        response = self._process_server_request(ptype, payload)
#            #rsock.send(str(response))
# #        else:
# #            self.warning('No manager reference')
# #
#        return response

# ===============================================================================
# SHMCommandProcessor
# ===============================================================================


# class SHMCommandProcessor(SHMServer):
#    '''
#    listens to a specified port for incoming requests.
#    request will come from the repeater
#    '''
#    #port = None
#    path = None
#
#    _listen = True
#    simulation = False
#    manager = None
#    def load(self, *args, **kw):
#        '''
#        '''
#        #grab the port from the repeater config file
#        config = self.get_configuration(path=os.path.join(paths.device_dir,
#                                                            'servers', 'repeater.cfg'))
#        if config:
# #            self.port = self.config_get(config, 'General', 'port', cast = 'int')
#            self.path = self.config_get(config, 'General', 'path')
#            return True
#
#    def close(self):
#        '''
#        '''
#        self._listen = False
#
#
#    def _handle(self, data):
#        '''
#
#        '''
#        self.debug('Received %s' % data)
#        response = None
#        if self.manager is not None:
#            type = None
#            if '|' in data:
#                type, data = data.split('|')
#
#            response = self.manager.process_server_request(type, data)
#
#            if isinstance(response, ErrorCode):
#                response = repr(response)
#
#            self.debug('Response %s' % response)
#        else:
#            self.warning('No manager reference')
#
#        return response
