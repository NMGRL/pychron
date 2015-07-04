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

# ============= enthought library imports =======================
from traits.api import HasTraits, String, Button, Int, Str, Enum, \
    Float, Bool, Event, Property, List
from traitsui.api import View, Item, HGroup, VGroup, ButtonEditor, EnumEditor

# ============= standard library imports ========================

# ============= local library imports  ==========================

# ============= views ===================================
# ============= EOF ====================================

import socket

# from timeit import Timer
import time
# import os
# from datetime import timedelta
from threading import Thread
import random
# import struct


class Client(HasTraits):
    command = Property(String('GetData', enter_set=True, auto_set=False),
                       depends_on='_command')
    _command = Str
    resend = Button
    receive_data_stream = Button
    response = String
    port = Int(1069)
#    port = Int(8080)
    # host = Str('192.168.0.65')
#    host = Str('129.138.12.145')
    host = 'localhost'
    path = None
    kind = Enum('IPC', 'UDP', 'TCP')

    period = Float(100)
    periodic = Event
    periodic_label = Property(depends_on='_alive')
    periods_completed = Int
    time_remain = Float
    n_periods = Int(100)
    _alive = Bool(False)

    calculated_duration = Property(depends_on=['n_periods', 'period'])

    ask_id = 'A'
    sent_commands = List
    pcommand = Str

    test_command = ''
    test_response = ''

    _sock = None
    def _get_calculated_duration(self):
        return self.period / 1000. * self.n_periods / 3600.

    def _periodic_fired(self):
        self._alive = not self._alive
        self.periods_completed = 0
        if self._alive:
            t = Thread(target=self._loop)
            t.start()

    def _loop(self):
        self.time_remain = self.calculated_duration
#        sock = self.get_connection()
        while self._alive and self.periods_completed <= self.n_periods:
            t = time.time()
            try:
                self._send(sock=None)

                self.time_remain = self.calculated_duration - self.periods_completed * self.period / 1000.0 / 3600.
                self.periods_completed += 1

                time.sleep(max(0, self.period / 1000.0 - (time.time() - t)))
            except Exception, e:
                print 'exception', e
        print 'looping complete'
        self._alive = False

    def _get_periodic_label(self):
        return 'Periodic' if not self._alive else 'Stop'

    def _resend_fired(self):
        self._send()

    def _set_command(self, v):
#    def _command_changed(self):
        self._command = v
        self.sent_commands.append(v)
        self._send()

    def _get_command(self):
        return self._command

    def _pcommand_changed(self):
        self._command = self._pcommand

    def _send(self, sock=None):
        if sock is None:
            sock = self._sock
            if sock is None:
                # open connection
                sock = self.get_connection()


        # send command
        sock.send(self.command)
        self.response = sock.recv(1024)
#        print self.response, 'foo'
        if 'ERROR' in self.response:
            print time.strftime('%H:%M:%S'), self.response
        return sock

    def get_connection(self, port=None):
        packet_kind = socket.SOCK_STREAM
        family = socket.AF_INET
        if port is None:
            port = self.port
        addr = (self.host, port)
#        print 'connection address', addr
        if self.kind == 'UDP':
            packet_kind = socket.SOCK_DGRAM

        elif self.kind == 'IPC':
            packet_kind = socket.SOCK_STREAM
            family = socket.AF_UNIX
            addr = self.path

        sock = socket.socket(family, packet_kind)
        sock.settimeout(5)
        print addr
        sock.connect(addr)
        return sock

    def ask(self, command, port=None, verbose=True):
        conn = self.get_connection(port=port)
        conn.send(command)
        r = None
        try:
            r = conn.recv(4096)
            r = r.strip()
            if verbose:
                print '{} -----ask----- {} ==> {}'.format(self.ask_id, command, r)
        except socket.error, e:
            print 'exception', e

        return r

    def test(self):
        ecount = 0
        for _ in range(2000):
            response = self.ask(self.test_command)
            if self.test_response:
                if response != self.test_response:
                    ecount += 1
                    print '&&&&&&&&&&&&&&&&& ERROR &&&&&&&&&&&&'
            time.sleep(random.randint(0, 100) / 10000.)
        print '=====test {} complete======'.format(self.ask_id)
        print '{} error count= {}'.format(self.ask_id, ecount)

#        self.ask('StartMultRuns Foo')
#        time.sleep(2)
#
#        self.ask('CompleteMultRuns Foo')

#        for i in range(500):
#            for v in 'ABCEDFG':
#
#                self.ask('GetValveState {}'.format(v))
#
#            if i % 5 == 0:
#                self.ask('Open {}'.format(self.ask_id[0]))
#            elif i % 8 == 0:
#                self.ask('Close {}'.format(self.ask_id[0]))
#
#            time.sleep(random.randint(0, 175) / 100.)

    def traits_view(self):
        v = View(
                 VGroup(
                     Item('receive_data_stream', show_label=False),
                     Item('command'),
                     Item('response', show_label=False, style='custom',
                          width=-300
                          ),
                     Item('pcommand', editor=EnumEditor(name='object.sent_commands')),
                     Item('resend', show_label=False),

                     HGroup(Item('periodic',
                                 editor=ButtonEditor(label_value='periodic_label'),
                                 show_label=False), Item('period', show_label=False),
                                 Item('n_periods'),
                                 Item('periods_completed', show_label=False)
                            ),
                     HGroup(Item('calculated_duration', format_str='%0.3f', style='readonly'),
                            Item('time_remain', format_str='%0.3f', style='readonly'),
                            ),
                     Item('kind', show_label=False),
                     Item('port'),
                     Item('host')),

                 resizable=True
                 )
        return v

def send_command(addr, cmd, kind='UDP'):
    p = socket.SOCK_STREAM
    if kind == 'UDP':
        p = socket.SOCK_DGRAM

    sock = socket.socket(socket.AF_INET, p)

    sock.connect(addr)
    sock.settimeout(2)
    sock.send(cmd)
    resp = sock.recv(1024)
    return resp

def client(kind, port):
    while 1:
        data = raw_input('    >> ')
        if kind == 'inet':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', port))
        else:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect("/tmp/hardware")

        s.send(data)
        datad = s.recv(1024)
        print 'Received', repr(datad)
        s.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 1063))

    cmd = 'Read bakeout1'
    s.send(cmd)
    s.recv(1024)
    s.close()

def main2():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/tmp/hardware')

    cmd = 'System|Read bakeout1'
    s.send(cmd)
    s.recv(1024)
    s.close()



def multiplex_test():
    # cmd = 'GetValveState C'
    c = Client(
               port=1067,
               ask_id='D'
               )

    c.test_command = 'GetPosition'
    c.test_response = '0.00,0.00,0.00'
    t = Thread(target=c.test)


    # cmd = 'GetValveState C'
    c = Client(
               port=1067,
               ask_id='E')
    c.test_command = 'SetLaserPower 10'
    c.test_response = 'OK'
    t2 = Thread(target=c.test)

    t.start()
    t2.start()

def diode_client():
    c = Client(
               port=1068,
               ask_id='D')
    c.configure_traits()

def co2_client():
    c = Client(

               port=1067,
               ask_id='E')
    c.configure_traits()
def system_client():
    c = Client(
               host='129.138.12.141',
               port=1061,
               ask_id='E')
    c.configure_traits()

def local_client():
    c = Client(
               path='/tmp/hardware-argus',
#               host=socket.gethostbyname(socket.gethostname()),
#               port=8900,
               ask_id='E')
    c.configure_traits()

def power_test():
        c = Client(
                   port=1068,
    #               host='129.138.12.141',
                    host='192.168.0.253',
                   ask_id='E')

        ask = c.ask
        ask('Enable')

        ask('SetLaserPower 10')
        time.sleep(4)
        ask('Disable')
#    for i in range(500):
#        print i
#        c.ask('Enable')
#        time.sleep(3)
#        c.ask('Disable')
#        time.sleep(1)

def timed_flag_test():
    c = Client(
              port=1061,
              ask_id='E')
    for _ in range(3):
        c.ask('Open ChamberPumpTimeFlag')

        while 1:

            if abs(float(c.ask('Read ChamberPumpTimeFlag'))) < 0.001:
                break
            time.sleep(1)
        time.sleep(1)


def mass_spec_param_test():
    c = Client(
              port=1061,
              ask_id='E')
    c.ask('Read test_param')
    c.ask('Read test_param1')
    c.ask('Read test_paramfoo')
    c.ask('Read pump_time')

def video_test():
    c = Client(
               port=1067,
               host='localhost',
               ask_id='E',
               kind='TCP')

    ask = c.ask
    for i in range(10):
        print 'executing run', i
        ask('Enable')

        time.sleep(5)
        ask('Disable')
        print 'finish run', i

        time.sleep(7)
if __name__ == '__main__':
    video_test()
#    local_client()
#    diode_client()
# 	system_client()
    # power_test()
    # plothist('benchmark_unix_only.npz')
#    benchmark('main()', 'from __main__ import main',
#              'benchmark_unix_tcp_no_log.npz'
#              )

#    multiplex_test()
#    laser_client()
#    power_test()
#    timed_flag_test()
#    mass_spec_param_test()
    # ===========================================================================
    # Check Remote launch snippet
    # ===========================================================================
    # ===========================================================================
    # def ready(client):
    #    r = client.ask('PychronReady')
    #    if r is not None:
    #        r = r.strip()
    #    return r == 'OK'
    #
    # c.port = 1063
    #
    # if not ready(c):
    #    print 'not ready'
    #    c.ask('RemoteLaunch')
    #    st = time.time()
    #    timeout = 5
    #    print 'launching'
    #    success = False
    #    while time.time() - st < timeout:
    #        if ready(c):
    #            success = True
    #            print 'Remotely launched !!!'
    #            break
    #
    #        time.sleep(2)
    #    if not success:
    #        print 'Launch timed out after {}'.format(timeout)
    # ===========================================================================


# ======================== EOF ===================================
#    def _receive_data_stream_fired(self):
#        sock = self.get_connection()
#        nbytes = sock.recv(4)
#        print nbytes, len(nbytes)
#        n = struct.unpack('!I', nbytes)[0]
#        print n
#        data = sock.recv(n)
#
#        #print struct.unpack('!d',data[:8])
#
#        ys = []
#        for i in range(0, n, 8):
#            ys.append(struct.unpack('>d', data[i:i + 8]))
#        plot(linspace(0, 6.28, n / 8), ys)
#        show()
#            print struct.unpack('!dd',data[i:i+16])
            # print struct.unpack('>d',data[i:i+8])
        # array(data, dtype='>'+'d'*400)
# def plothist(name):
#    p = os.path.join(os.getcwd(), name)
#    files = load(p)
#    hist(files['times'], 1000 / 4.)
#    xlim(0, 0.040)
#    show()
#
# def benchmark(me, im, fp):
#    t = Timer(me, im)
#    st = time.time()
#    n = 1000
#    times = array(t.repeat(n, number=1))
#    dur = time.time() - st
#
#    etime = timedelta(seconds=dur)
#    avg = mean(times)
#    stdev = std(times)
#    mi = min(times) * 1000
#    ma = max(times) * 1000
#
#    print 'n trials', n, 'execution time %s' % etime
#    print 'mean %0.2f' % (avg * 1000), ' std %0.2f' % (stdev * 1000)
#    print 'min %0.2f ms' % mi, 'max %0.2f ms' % ma
#
#    stats = array([n, etime, avg, stdev, mi, ma])
#    p = os.path.join(os.getcwd(), fp)
#    savez(p, times=times, stats=stats)
#
#    foo = load(p)
#    hist(foo['times'], n / 4.)
#    show()

#    host = '129.138.12.145'
#
# #    host = 'localhost'
#    port = 1069
#    cmds = ['SetIntegrationTime 1.048576']
# #    cmds = ['GetHighVoltage', 'GetTrapVoltage']
#    #cmds = ['DoJog standard_short']
#    for c in cmds:
#        r = send_command((host, port), c)
#        print '{} ===> {}'.format(c, r)
