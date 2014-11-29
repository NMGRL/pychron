# ===============================================================================
# Copyright 2012 Jake Ross
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

version_id = '_test'
from helpers import build_version
build_version(version_id)

# ============= enthought library imports =======================
from traits.api import Int, Bool, Event, Property
from traitsui.api import View, Item, ButtonEditor
# ============= standard library imports ========================
import SocketServer
import shlex
import socket
from threading import Thread
# ============= local library imports  ==========================

cnt = 0
gErrorSet = False

from pychron.loggable import Loggable

class UDPVerboseServer(SocketServer.UDPServer):
    logger = None

class TCPVerboseServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    logger = None

class IPCVerboseServer(SocketServer.ThreadingMixIn, SocketServer.UnixStreamServer):
    logger = None

class Server(Loggable):
    port = Int(8000)
    host = None
    state_button = Event
    state_label = Property(depends_on='_alive')
    _alive = Bool(False)
    def _get_state_label(self):
        return 'Stop' if self._alive else 'Start'

    def _state_button_fired(self):
        if self._alive:
            self.server.shutdown()

        else:
            self.start_server()

        self._alive = not self._alive

    def start_server(self):
        host = self.host
        if host is None:
            host = socket.gethostbyname(socket.gethostname())

        port = self.port
        self.info('Starting server {} {}'.format(host, port))
        t = Thread(name='serve', target=self._serve, args=(host, port))
        t.start()

    def _serve(self, host, port):
#        self.server = server = SocketServer.UDPServer((host, port), EmulatorHandler)
        server = TCPVerboseServer((host, port), EmulatorHandler)
#        server = IPCVerboseServer(host, EmulatorHandler)
#        server = IPCVerboseServer(host, EmulatorHandler)
#        server = IPCVerboseServer(host, EmulatorHandler)
#        server = LinkServer()
        server.info = self.info
        # server.allow_reuse_address = True
        self.server = server

        server.socket.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
#        server.start_server(host)
        server.serve_forever()

    def traits_view(self):
        v = View(Item('state_button', show_label=False,
                    editor=ButtonEditor(label_value='state_label')
                    ),

                 Item('port'),

                 title='Emulator'
                 )

        return v

def verbose(func):
    def _verbose(obj, *args, **kw):
        result = func(obj, *args, **kw)

        obj.logger.info('Func={} args={}'.format(func.__name__,
                                  ','.join(map(str, args))
                                  ))
        return result

    return _verbose
#
def verbose_all(cls):
    import inspect
    for name, m in inspect.getmembers(cls, inspect.ismethod):
        if name.startswith('handle'):
            setattr(cls, name, verbose(m))
    return cls
#
@verbose_all
class QtegraEmulator(Loggable):
    # ===========================================================================
    # Qtegra Protocol
    # ===========================================================================
    def handleSetMass(self, mass):
        mass = float(mass)
#        print 'setting mass %f' % mass
        return 'OK'

    def handleGetData(self, *args):
        d = [
            [36, 0.01, 1.5],
            [37, 0.1, 1.5],
            [38, 1, 1.5],
            [39, 10, 1.5],
            [40, 100, 1.5],
            ]
        return '\n'.join([','.join(map('{:0.3f}'.format, r)) for r in d])

#    def GetDataNow(self, *args):
# #        print 'get data now'
#        return self.GetData(*args)

    def handleGetCupConfigurations(self, *args):
#        print 'get cup configurations'
        return ','.join(['Argon'])

    def handleGetSubCupConfigurations(self, cup_name):
#        print 'get sub cup configurations for %s' % cup_name
        return ','.join(['A', 'B', 'C', 'X'])

    def handleActivateCupConfiguration(self, names):
        cup_name, sub_cup_name = names.split(',')
        return 'OK'

    def handleSetIntegrationTime(self, itime):
        return 'OK'

    def handleGetTuneSettings(self, *args):
        return ','.join(['TuneA', 'TuneB', 'TuneC', 'TuneD'])

    def handleSetTuning(self, name):
        return 'OK'

    def handlePychronReady(self):
        global cnt
        cnt = 0
        return 'OK'

    def handleGetHighVoltage(self, *args):
        return '4500'
    def handleSetHighVoltage(self, *args):
        return 'OK'

    def handleSetTrapVoltage(self, *args):
        return 'OK'
    def handleGetTrapVoltage(self, *args):
        return 10

    def handleGetIonCounterVoltage(self, *args):
        return 10
    def handleSetIonCounterVoltage(self, *args):
        return 'OK'

    def handleGetIonRepeller(self, *args):
        return 10
    def handleSetIonRepeller(self, *args):
        return 'OK'

    def handleGetDeflection(self, *args):
        return 10
    def handleSetDeflection(self, *args):
        return 'OK'

    def handleGetZSymmetry(self, *args):
        return 10
    def handleSetZSymmetry(self, *args):
        return 'OK'

    def handleGetYSymmetry(self, *args):
        return 10
    def handleSetYSymmetry(self, *args):
        return 'OK'

    def handleGetExtractionLens(self, *args):
        return 10
    def handleSetExtractionLens(self, *args):
        return 'OK'

    def handleGetZFocus(self, *args):
        return 10
    def handleSetZFocus(self, *args):
        return 'OK'

    def handleGetElectronEnergy(self, *args):
        return 10
    def handleSetElectronEnergy(self, *args):
        return 'OK'

    def handleGetMagnetDAC(self, *args):
        return 10
    def handleSetMagnetDAC(self, *args):
        return 'OK'

    def handleBlankBeam(self, *args):
        return 'OK'

    def handleReadTest(self, *args):
        global cnt
        cnt += 1
        r = cnt
        if cnt > 11:
            cnt = 0
        return str(r)

    def handleSendTest(self, *args):
        return "OK"

    def handleWatch(self, *args):
        global gErrorSet
        gErrorSet = True

@verbose_all
class LaserEmulator(Loggable):
    _position = '1,2,3'
    def handlePychronReady(self):
        return 'OK'
    def handleSetLaserPower(self, p):
        return 'OK'
    def handleEnableLaser(self):
        return 'OK'
    def handleDisableLaser(self):
        return 'OK'

    def handleGetPosition(self):
        return self._position

    def handleSetXY(self, xy):
        self._position = xy + ',5'

    def handleGetBeamDiameter(self):
        return 0
    def handleSetBeamDiameter(self, v):
        return 0
    def handleGetLaserStatus(self):
        return 'OK'
    def handleGetZoom(self):
        return 0
    def handleSetSampleHolder(self, v):
        return 'OK'

_state = True

@verbose_all
class ExtractionLineEmulator(Loggable):

    def handleOpen(self, name):
        return 'OK'
    def handleClose(self, name):
        return 'OK'

    def handleGetValveState(self, name):
        global _state
        _state = not _state
        return str(_state)

    def handleGetValveStates(self):
        keys = 'ABCDEF'
        states = ('1',) * len(keys)
        return ''.join(['{}{}'.format(*a) for a in zip(keys, states)])

    def handleGetValveLockStates(self):
        print 'geting lock staes'
        keys = 'ABCDEF'
        states = ('0',) * len(keys)
        return ''.join(['{}{}'.format(*a) for a in zip(keys, states)])

    def handleGetError(self):
        return '103 testerror'

class EmulatorHandler(SocketServer.BaseRequestHandler):

    # ===========================================================================
    # BaseRequestHandler protocol
    # ===========================================================================
#    def __init__(self, *args, **kw):
#        super(EmulatorHandler, self).__init__(*args, **kw)
#        QtegraEmulator.__init__(self, **kw)
    def __init__(self, *args):
        self._qtegra_em = QtegraEmulator()
        self._el_em = ExtractionLineEmulator()
        self._laser_em = LaserEmulator()
        SocketServer.BaseRequestHandler.__init__(self, *args)

    def handle(self):
        new_line = lambda x: '{}\n\r'.format(x)

        data = self.request.recv(2 ** 8)

        data = data.strip()
        if ':' in data:
            datargs = data.split(':')
        else:
            datargs = shlex.split(data)
        try:
            cmd = datargs[0]


            try:
                args = tuple(datargs[1:])
            except IndexError:
                args = tuple()

            try:
                func = None
                for name in ['qtegra', 'el', 'laser']:

                    obj = getattr(self, '_{}_em'.format(name))
                    try:
                        func = getattr(obj, 'handle{}'.format(cmd))
                        break
                    except AttributeError, e:
                        continue
                    except Exception, e:
                        print e

                else:
                    result = 'Error: Command {} not available'.format(cmd)

                if func:
                    try:
                        result = str(func(*args))
                    except TypeError:
                        result = 'Error: Invalid parameters %s passed to %s' % (args, cmd)
            except AttributeError:
                result = 'Error: Command {} not available'.format(cmd)
        except IndexError:
            result = 'Error: poorly formatted command {}'.format(data)

        global gErrorSet
#        self.request.send('OK' + '\n\r')
        if gErrorSet:
            result = 'error: 101'
            gErrorSet = False

        self.server.info('received ({}) - {}, {}'.format(len(data), data, result))
        self.request.sendall(new_line(result))
        self.server.info('sent {}'.format(result))

if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('emulator')

#    p = '/tmp/hardware-argus'
#    if os.path.exists(p):
#        os.remove(p)

#    s = Server(host=p)
#    s = Server(host='192.168.0.253')
    s = Server(host='localhost')

    s.start_server()
    s.configure_traits()
#    portn = 8000
#    s = Server()

#    ls = LinkServer()
#    ls.start_server('129.138.12.138', 1070)

#    s.start_server('localhost', portn)
# ============= EOF =============================================

# ===============================================================================
# link
# ===============================================================================
# class LinkServer(Loggable):
#    def start_server(self, host, port):
#        self.info('Link Starting server {} {}'.format(host, port))
#        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        server.bind((host, port))
#        server.listen(5)
#        input = [server, sys.stdin]
#        running = 1
#        c = LinkEmulator()
#        while running:
#            inputready, _outputready, _exceptready = select.select(input, [], [])
#            for s in inputready:
#
#                if s == server:
#                    # handle the server socket
#                    client, _address = server.accept()
#                    input.append(client)
#
#                elif s == sys.stdin:
#                    # handle standard input
#                    _junk = sys.stdin.readline()
#                    running = 0
#
#                else:
#                    # handle all other sockets
#
#                    c.request = s
#                    data = c.handle()
#                    if data:
#                        try:
#                            s.send(data)
#                        except socket.error:
#                            pass
#                    else:
#                        s.close()
#                        input.remove(s)
#        server.close()
# class LinkEmulator(Emulator):
#    def handle(self):
#        try:
#            data = self.request.recv(1024).strip()
#        except socket.error:
#            return
#
#        if not data:
#            return
#
#        print 'recieved (%i) - %s' % (len(data), data)
#        if ':' in data:
#            datargs = data.split(':')
#        else:
#            datargs = shlex.split(data)
#
#        try:
#            cmd = datargs[0]
#            args = tuple(datargs[1:])
#            try:
#                func = getattr(self, cmd)
#                try:
#                    result = str(func(*args))
#                except TypeError:
#                    result = 'Error: Invalid parameters %s passed to %s' % (args, cmd)
#            except AttributeError:
#                result = 'Error: Command %s not available' % cmd
#        except IndexError:
#            result = 'Error: poorly formatted command %s' % data
#
#        return result
# class LinkHandler(QtegraEmulator):
#    request = None
#    def handle(self):
#        new_line = lambda x: '{}\n\r'.format(x)
#        #udp
# #        data = self.request[0].strip()
#
#        #ipc
#        print 'handle'
#        print self.request.recv(1024)
#        self.request.sendall(new_line('OK'))

