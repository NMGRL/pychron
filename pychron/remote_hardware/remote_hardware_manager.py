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
from traits.api import Dict, Bool, on_trait_change, List
from apptools.preferences.preference_binding import bind_preference
from traitsui.api import View, Item, Group, HGroup, VGroup, \
    ListEditor, TableEditor
from traitsui.table_column import ObjectColumn
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.remote_hardware.command_processor import CommandProcessor
from pychron.messaging.remote_command_server import RemoteCommandServer
from pychron.globals import globalv
from pychron.paths import paths

# from pychron.messaging.directory_server import DirectoryServer
# from threading import Thread

'''
#===================================
@todo
    add get_error_status
    add get list of files
    
#===================================
'''


class RemoteHardwareManager(Manager):
    processors = Dict
    servers = List(RemoteCommandServer)

#    directory_server = Instance(DirectoryServer, ())
    enable_hardware_server = Bool
#    enable_directory_server = Bool
    result = None
    system_lock = Bool(False)


    def bind_preferences(self, cp):
        try:
            bind_preference(self, 'system_lock', 'pychron.hardware.enable_system_lock')

            bind_preference(cp, 'system_lock', 'pychron.hardware.enable_system_lock')
            bind_preference(cp, 'system_lock_address', 'pychron.hardware.system_lock_address')
            bind_preference(cp, 'system_lock_name', 'pychron.hardware.system_lock_name')

    #        ip = InitializationParser(os.path.join(setup_dir, 'initialization.xml'))
            ip = InitializationParser()
            names = []
            hosts = dict()
            for name, host in ip.get_systems():
                names.append(name)
                hosts[name] = host

            pref = self.application.preferences
            pref.set('pychron.hardware.system_lock_names', names)
            pref.set('pychron.hardware.system_lock_addresses', hosts)

            name = pref.get('pychron.hardware.system_lock_name')

            try:
                if name:
                    pref.set('pychron.hardware.system_lock_address',
                              hosts[name.strip("'").lower()])
                else:
                    pref.set('pychron.hardware.system_lock_address',
                              hosts[names[0].lower()])
            except Exception, err:
                pass
    #            import traceback
    #            traceback.print_exc()
    #            print 'system lock exception', err

            pref.save()
        except AttributeError:
            pass

#        ds = self.directory_server
#        bind_preference(ds, 'host', 'pychron.hardware.directory_server_host')
#        bind_preference(ds, 'port', 'pychron.hardware.directory_server_port')
#        bind_preference(ds, 'root', 'pychron.hardware.directory_server_root')


    def validate_address(self, addr):

        if self.system_lock:
            addrs = self.application.preferences.get('pychron.hardware.system_lock_addresses')
            pairs = addrs[1:-1].split(',')

            for p in pairs:
                k, v = p.split(':')
                k = k.strip()
                v = v.strip()
                if v[1:-1] == addr:
                    return k
            self.warning('You are not using an approved ip address {}'.format(addr))
        else:
            return addr

    def lock_by_address(self, addr, lock=True):
        if lock:
            name = self.validate_address(addr)
            if name is not None:
                self.application.preferences.set('pychron.hardware.system_lock_address', addr)
                self.application.preferences.set('pychron.hardware.system_lock_name', name)
                return True

        else:
            self.application.preferences.set('pychron.hardware.enable_system_lock', lock)
            return True

    def get_server_response(self):
        return self.result

    def bootstrap(self):
        if self.enable_hardware_server:

            if globalv.use_ipc:
                for p in self.processors.itervalues():
                    self.info('bootstrapping {}'.format(p.name))
                    p.manager = self
                    p.bootstrap()
            else:
                self._load_servers()

#        if self.enable_directory_server:
#            self._load_directory_server()

    def stop(self):
        for p in self.processors.itervalues():
            p.close()

#        self.directory_server.stop()
# ===============================================================================
# private
# ===============================================================================
    def _load_servers(self):
        '''
        '''
        # get server names
        ip = InitializationParser()
        names = ip.get_servers()
        if names:
            for s in names:
                pn = '{}-processor'.format(s)
                cp = self._command_processor_factory(name=pn)
                cp.manager = self
                cp.bootstrap()

                self.processors[pn] = cp
                e = RemoteCommandServer(name=s,
                       configuration_dir_name='servers',
                       processor=cp
                       )
                e.bootstrap()
                self.servers.append(e)

#    def _load_directory_server(self):
#        t = Thread(target=self.directory_server.start)
#        t.start()

# ===============================================================================
# handlers
# ===============================================================================
    @on_trait_change('enable_hardware_server')
    def enabled_changed(self):
        if self.enable_hardware_server:
            self.bootstrap()
        else:
            self.stop()

    def _command_processor_factory(self, path=None, name=None):
        if name is None:
            if path is not None:
                name = path.split('-')[-1]

        cp = CommandProcessor(application=self.application,
                              path=path,
                              name=name)

        self.bind_preferences(cp)

        return cp


    def traits_view(self):
        '''
        '''
        cols = [ObjectColumn(name='name'),
                ObjectColumn(name='klass', label='Class'),
                ObjectColumn(name='processor_type', label='Type'),
              ObjectColumn(name='host'),
              ObjectColumn(name='port')]
        tservers = Group(Item('servers', style='custom',
                      editor=TableEditor(columns=cols,
                                           selected='selected',
                                           editable=False),
                      show_label=False,
                      ),
                      show_border=True,
                      label='Servers'
                      )
        servers = Item('servers',
                       style='custom',
                       editor=ListEditor(use_notebook=True,
                                           page_name='.name',
                                           selected='selected'), show_label=False)
#        repeater = Group(Item('repeater', style='custom',
#                              show_label=False),
#                            show_border=True,
#
#                         label='Repeater')
        v = View(HGroup(
                 VGroup(tservers),
                 servers
                 ),
                 title='Remote Hardware Server',
                 width=700,
                 height=360,
                 resizable=True,
                 handler=self.handler_klass
                 )

        return v

# ===============================================================================
# defaults
# ===============================================================================
    def _processors_default(self):
        ps = dict()
        ip = InitializationParser()

        hosts = []
        # load the hosts file
        p = os.path.join(paths.setup_dir, 'hosts')
        if os.path.isfile(p):
            with open(p, 'r') as f:
                hosts = [l.strip() for l in f if l.strip()]

        for pi in ip.get_processors():
            cp = self._command_processor_factory(path=pi)
            cp._hosts = hosts

            ps[cp.name] = cp

        return ps
#============= EOF ====================================
#    def process_server_request(self, request_type, data):
#        '''
#
#        '''

#        self.debug('Request: {}, {}'.format(request_type, data.strip()))
#        result = 'error handling'
#
#        if not request_type in ['System', 'Diode', 'Synrad', 'CO2', 'test']:
#            self.warning('Invalid request type ' + request_type)
#        elif request_type == 'test':
#            result = data
#        else:
#
#            klass = '{}Handler'.format(request_type.capitalize())
#            pkg = 'pychron.remote_hardware.handlers.{}_handler'.format(request_type.lower())
#            try:
#
#
#                module = __import__(pkg, globals(), locals(), [klass])
#
#                factory = getattr(module, klass)
#
#                handler = factory(application=self.application)
#                '''
#                    the context filter uses the handler object to
#                    get the kind and request
#                    if the min period has elapse since last request or the message is triggered
#                    get and return the state from pychron
#
#
#                    pure frequency filtering could be accomplished earlier in the stream in the
#                    Remote Hardware Server (CommandRepeater.get_response)
#                '''
#
#
#                result = self.context_filter.get_response(handler, data)
#
#            except ImportError, e:
#                result = 'ImportError klass={} pkg={} error={}'.format(klass, pkg, e)
#
#        self.debug('Result: {}'.format(result))
#        if isinstance(result, ErrorCode):
#            self.result = repr(result)
#        else:
#            self.result = result
#
#        return result
