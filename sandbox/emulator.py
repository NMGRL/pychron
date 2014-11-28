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

import SocketServer
import shlex
import sys
import select
import socket


class Server(object):
    def start_server(self, host, port):
        print 'Starting server {} {}'.format(host, port)
        server = SocketServer.TCPServer((host, port), Emulator)
        server.allow_reuse_address = True
        server.serve_forever()


class LinkServer(object):
    def start_server(self, host, port):
        print 'Link Starting server {} {}'.format(host, port)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(5)
        input_ = [server, sys.stdin]
        running = 1
        c = LinkEmulator()
        while running:
            inputready, _outputready, _exceptready = select.select(input_, [], [])
            for s in inputready:

                if s == server:
                    # handle the server socket
                    client, _address = server.accept()
                    input_.append(client)

                elif s == sys.stdin:
                    # handle standard input_
                    _junk = sys.stdin.readline()
                    running = 0

                else:
                    # handle all other sockets

                    c.request = s
                    data = c.handle()
                    if data:
                        try:
                            s.send(data)
                        except socket.error:
                            pass
                    else:
                        s.close()
                        input_.remove(s)
        server.close()


class Emulator(object):
    cnt = 0
    state = '1'
    #===========================================================================
    # Pychron
    #===========================================================================

    def Open(self, name):
        print 'Open Valve - %s' % name
        self.state = '1'
        return 'OK'

    def Close(self, name):
        self.state = '0'
        print 'Close Valve - %s' % name
        return 'OK'

    def GetValveState(self, name):
        print 'Get valve state - %s' % name
        return 'True'

    def GetValveStates(self, *args):
        r = 'T0'
        # if self.cnt%2==0:
        #    r='T1'

        #        self.cnt+=1
        #        r='T'+self.state
        print 'Get valve states ', r
        return r

        return ''.join(['A', '0',
                        'B', '1',
                        'C', '1',
                        'D', '0',
                        'E', '1',
                        'F', '1',
                        'G', '0',
        ])

    def GetManualState(self, name):
        print 'Get manual state - %s' % name
        return 'False'

    def SetLaserPower(self, pwr):
        print 'Set laser power - %s' % pwr
        return 'OK'

    def ReadLaserPower(self, *args):
        print 'Read laser power'
        return '10'

    def GetLaserStatus(self):
        return 'OK'

    def Enable(self, *args):
        print 'Enable'
        return 'OK'

    def Disable(self, *args):
        print 'Disable'
        return 'OK'

    def SetXY(self, data):
        x, y = data.split(',')
        x = float(x)
        y = float(y)
        print 'Set XY - %f, %f' % (x, y)
        return 'OK'

    def GetPosition(self):
        print 'Get Position'
        return '10.1,10.2,10.3'

    def SetZ(self, data):
        print 'Set Z - %s' % data
        return 'OK'

    def GetDriveMoving(self, *args):
        print 'Get Drive Moving'
        return 'False'

    def StopDrive(self, *args):
        print 'Stop Drive'
        return 'OK'

    def SetDriveHome(self, *args):
        print 'Set Drive Home'
        return 'OK'

    def GetJogProcedures(self, *args):
        print 'Get Jog Procedures'
        return ','.join(['JogA', 'JogB', 'JogC'])

    def DoJog(self, jog_name):
        print 'Do jog - %s' % jog_name
        return 'OK'

    def SetBeamDiameter(self, data):
        print 'Set beam diameter - %s' % data
        return 'OK'

    def SetZoom(self, data):
        print 'Set zoom - %s' % data
        return 'OK'

    def Read(self, name):
        print 'reading %s' % name
        return 10.5

    def Set(self, name, value):
        print 'setting %s to %s' % (name, value)
        return 'OK'

    #===========================================================================
    # Qtegra Protocol
    #===========================================================================
    def SetMass(self, mass):
        mass = float(mass)
        print 'setting mass %f' % mass
        return 'OK'

    def GetData(self, *args):
        print 'get data'
        d = [
            [36, 0.01, 1.5],
            [37, 0.1, 1.5],
            [38, 1, 1.5],
            [39, 10, 1.5],
            [40, 100, 1.5],
        ]
        return '\n'.join([','.join(['%f' % ri for ri in r]) for r in d])

    def GetDataNow(self, *args):
        print 'get data now'
        return self.GetData(*args)

    def GetCupConfigurations(self, *args):
        print 'get cup configurations'
        return ','.join(['Argon'])

    def GetSubCupConfigurations(self, cup_name):
        print 'get sub cup configurations for %s' % cup_name
        return ','.join(['A', 'B', 'C', 'X'])

    def ActivateCupConfiguration(self, names):
        cup_name, sub_cup_name = names.split(',')
        print 'activating %s %s' % (cup_name, sub_cup_name)
        return 'OK'

    def SetIntegrationTime(self, itime):
        print 'setting integration time %s' % itime
        return 'OK'

    def GetTuneSettings(self, *args):
        print 'get tune settings'
        return ','.join(['TuneA', 'TuneB', 'TuneC', 'TuneD'])

    def SetTuning(self, name):
        print 'set tuning %s' % name
        return 'OK'


class EmulatorHandler(SocketServer.BaseRequestHandler, Emulator):
    #===========================================================================
    # BaseRequestHandler protocol
    #===========================================================================

    def handle(self):
        data = self.request.recv(1024).strip()

        if ':' in data:
            datargs = data.split(':')
        else:
            datargs = shlex.split(data)

        try:
            cmd = datargs[0]
            args = tuple(datargs[1:])
            try:
                func = getattr(self, cmd)
                try:
                    result = str(func(*args))
                except TypeError:
                    result = 'Error: Invalid parameters %s passed to %s' % (args, cmd)
            except AttributeError:
                result = 'Error: Command %s not available' % cmd
        except IndexError:
            result = 'Error: poorly formatted command %s' % data

        print 'recieved (%i) - %s, %s' % (len(data), data, result)
        self.request.send(result + '\n')


class LinkEmulator(Emulator):
    def handle(self):
        try:
            data = self.request.recv(1024).strip()
        except socket.error:
            return

        if not data:
            return

        print 'recieved (%i) - %s' % (len(data), data)
        if ':' in data:
            datargs = data.split(':')
        else:
            datargs = shlex.split(data)

        try:
            cmd = datargs[0]
            args = tuple(datargs[1:])
            try:
                func = getattr(self, cmd)
                try:
                    result = str(func(*args))
                except TypeError:
                    result = 'Error: Invalid parameters %s passed to %s' % (args, cmd)
            except AttributeError:
                result = 'Error: Command %s not available' % cmd
        except IndexError:
            result = 'Error: poorly formatted command %s' % data

        return result


if __name__ == '__main__':
    args = sys.argv[1:]

    portn = 1059
    if len(args) == 1:
        portn = int(args[0])

    #    s = Server()
    #    s.start_server('129.138.12.138', portn)

    ls = LinkServer()
    ls.start_server('129.138.12.138', 1070)

#    s.start_server('localhost', portn)
