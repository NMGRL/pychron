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
from traits.api import  Str, Int, Instance, Bool, Property, Event, Button, String
from traitsui.api import View, Item, Group, HGroup, VGroup, \
    ButtonEditor, Handler
from pyface.timer.api import Timer
#============= standard library imports ========================
import threading
import datetime
import select
import socket
import os
#============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
from pychron.messaging.command_repeater import CommandRepeater
from pychron.core.helpers.datetime_tools import diff_timestamp
from pychron.remote_hardware.command_processor import CommandProcessor
from pychron.core.ui.led_editor import LED, LEDEditor
from pychron.globals import globalv

LOCAL = False
class RCSHandler(Handler):
    def init(self, info):
        '''
        '''
        obj = info.object
        if obj._running:
            obj.led.state = 2
    def object__running_changed(self, info):
        '''
           
        '''
        if info.initialized:
            obj = info.object
            if obj._running:
                obj.led.state = 2
            else:
                obj.led.state = 0

class RemoteCommandServer(ConfigLoadable):
    '''
    '''
    simulation = False
    _server = None
    repeater = Instance(CommandRepeater)
    processor = Instance(CommandProcessor)

    host = Str(enter_set=True, auto_set=False)
    port = Int(enter_set=True, auto_set=False)
    klass = Str

    loaded_port = None
    loaded_host = None

    packets_received = Int
    packets_sent = Int
    repeater_fails = Int

    cur_rpacket = String
    cur_spacket = String

    server_button = Event
    server_label = Property(depends_on='_running')
    _running = Bool(False)
    _connected = Bool(False)

    save = Button
    _dirty = Bool(False)

    run_time = Str
    led = Instance(LED, ())

    use_ipc = True

    def _repeater_default(self):
        '''
        '''
        if globalv.use_ipc:
            c = CommandRepeater(
                        logger_name='{}_repeater'.format(self.name),
                        name=self.name,
                           configuration_dir_name='servers')
            if c.bootstrap():
                return c

    def _repeater_fails_changed(self, old, new):
        if new != 0:
            self.repeater.led.state = 0

    def load(self, *args, **kw):
        '''
        '''

        config = self.get_configuration()
        if config:



            server_class = self.config_get(config, 'General', 'class')
            if server_class is None:
                return

            if server_class == 'IPCServer':
                path = self.config_get(config, 'General', 'path')
                if path is None:
                    self.warning('Path not set. use path config value')
                    return
                addr = path
                self.host = path
                if os.path.exists(path):
                    os.remove(path)
            else:
                if LOCAL:
                    host = 'localhost'
                else:
                    host = self.config_get(config, 'General', 'host', optional=True)
                port = self.config_get(config, 'General', 'port', cast='int')

                if host is None:
                    host = socket.gethostbyname(socket.gethostname())
                if port is None:
                    self.warning('Host or Port not set {}:{}'.format(host, port))
                    return
                elif port < 1024:
                    self.warning('Port Numbers < 1024 not allowed')
                    return
                addr = (host, port)

                self.host = host
                self.port = port if port else 0

                self.loaded_host = host
                self.loaded_port = port
            self.klass = server_class[:3]

            ds = None
            if config.has_option('Requests', 'datasize'):
                ds = config.getint('Requests', 'datasize')

            ptype = self.config_get(config, 'Requests', 'type', optional=False)
            if ptype is None:
                return

            self.datasize = ds
            self.processor_type = ptype



            self._server = self.server_factory(server_class, addr, ptype, ds)

            # add links
            for link in self.config_get_options(config, 'Links'):
                # note links cannot be stopped
                self._server.add_link(link,
                                       self.config_get(config, 'Links', link))

            if self._server is not None and self._server.connected:
                addr = self._server.server_address
#                saddr = '({})'.format(','.join(addr if isinstance(addr, tuple) else (addr,)))
                saddr = '({})'.format(addr)
                msg = '%s - %s' % (server_class, saddr)
                self.info(msg)
                self._connected = True
                return True
            else:
                self._connected = False
                self.warning('Cannot connect to {}'.format(addr))


    def server_factory(self, klass, addr, ptype, ds):
        '''
        '''
        # from tcp_server import TCPServer
        # from udp_server import UDPServer

        module = __import__('pychron.messaging.{}_server'.format(klass[:3].lower()), fromlist=[klass])
        factory = getattr(module, klass)

#        gdict = globals()
#        if handler in gdict:
#            handler_klass = gdict[handler]

#        server = gdict[server_class]
        if ds is None:
            ds = 2 ** 10
#        return server(self, ptype, ds, addr, handler_klass)
        return factory(self, ptype, ds, addr)

    def open(self):
        '''
        '''
        self._running = True
        # t = threading.Thread(target = self._server.serve_forever)
        t = threading.Thread(target=self.start_server)
        t.start()

        return True

    def start_server(self):
        SELECT_TIMEOUT = 1
#        THREAD_LIMIT = 15
        while self._running:
            try:
                readySocket = select.select([self._server.socket], [],
                                            [], SELECT_TIMEOUT)
                if readySocket[0]:
                    self._server.handle_request()
#                    if threading.activeCount() < THREAD_LIMIT:
#                        self._server.handle_request()

            except:
                pass
#        self._server.socket.close()

    def shutdown(self):
        '''
        '''
        self._connected = False
        if self._server is not None:
#            self._server.shutdown()
            self._server.socket.close()

            self._running = False

    def traits_view(self):
        '''
        '''
        cparams = VGroup(
                        HGroup(
                                Item('led', show_label=False,
                                     editor=LEDEditor()),
                                Item('server_button', show_label=False,
                                     editor=ButtonEditor(label_value='server_label'),
                                     enabled_when='_connected'),
                                ),

                        Item('host', visible_when='not _running'),
                        Item('port', visible_when='not _running'),

                        show_border=True,
                        label='Connection',
                        )
        stats = Group(
                      Item('packets_received', style='readonly'),
                      Item('cur_rpacket', label='Received', style='readonly'),
                      Item('packets_sent', style='readonly'),
                      Item('cur_spacket', label='Sent', style='readonly'),

                      Item('repeater_fails', style='readonly'),
                      Item('run_time', style='readonly'),
                      show_border=True,
                      label='Statistics',
                      visible_when='_connected'
                      )

        buttons = HGroup(
                         Item('save', show_label=False, enabled_when='_dirty')
                         )
        v = View(VGroup(
                        cparams,
                        stats,
                        buttons
                        ),
                handler=RCSHandler,
               )
        return v

    def _run_time_update(self):
        '''
        '''

#        t = datetime.datetime.now() - self.start_time

#        h = t.seconds / 3600
#        m = (t.seconds % 3600) / 60
#        s = (t.seconds % 3600) % 60

        t, h, m, s = diff_timestamp(datetime.datetime.now(), self.start_time)


        rt = '{:02n}:{:02n}:{:02n}'.format(h, m, s)
        if t.days:
            rt = '{} {:02n}:{:02n}:{:02n}' .format(t.days, h, m, s)
        self.run_time = rt

    def __running_changed(self):
        '''
        '''
        if self._running:
            self.start_time = datetime.datetime.now()
            self.timer = Timer(1000, self._run_time_update)
        else:
            self.timer.Stop()

    def _anytrait_changed(self, name, value):
        '''

        '''
        if name in ['host', 'port']:
            attr = 'loaded_{}'.format(name)
            a = getattr(self, attr)
            if value != a and a is not None:
                self._dirty = True

    def _save_fired(self):
        '''
        '''

        self.shutdown()
        config = self.get_configuration()
        for attr in ['host', 'port']:
            a = getattr(self, attr)
            setattr(self, 'loaded_{}'.format(attr), a)
            config.set('General', attr, a)
            self.write_configuration(config)
            self.load()
        self._dirty = False

    def _server_button_fired(self):
        '''
        '''
        if self._running:
            self.shutdown()
        else:
            # reset the stats
            self.packets_received = 0
            self.packets_sent = 0
            self.cur_rpacket = ''
            self.cur_spacket = ''
            self.repeater_fails = 0

#            self._server = self.server_factory('TCPServer',
#                                               (self.host, self.port),
#                                               self.handler,
#                                               self.processor_type,
#                                               self.datasize
#                                             )
#            self.open()
            self.bootstrap()

    def _get_server_label(self):
        '''
        '''
        return 'Start' if not self._running else 'Stop'

#============= EOF ====================================

#            if self._server is not None:
#                sa = self._server.server_address
#                '''
#                    BUG
#                    1. start _server with 129.138.12.141
#                        _server responds to commands sent to 129.138.12.141
#
#                    2. reinitialize _server with 129.138.12.140
#                        _server still responds to commands sent to 129.138.141
#                '''
#                if sa != addr:
#
#
#                    self.warning('Reinitialization of _server not allowed- restart program to alter _server parameters')
#            else:
