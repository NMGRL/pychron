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
from traits.api import List, Instance, on_trait_change
from traitsui.api import View, Item, Group, HGroup, VGroup, \
    ListEditor, TableEditor, InstanceEditor
from traitsui.table_column import ObjectColumn

#============= standard library imports ========================
import os
import ConfigParser
#============= local library imports  ==========================
from pychron.messaging.command_repeater import CommandRepeater
from pychron.messaging.remote_command_server import RemoteCommandServer
from pychron.managers.manager import Manager, AppHandler
from pychron.paths import paths
from pychron.core.helpers.timer import Timer
from pychron.messaging.directory_server import DirectoryServer

class RemoteHardwareServerManager(Manager):
    '''
    '''
#    display = Any
    servers = List(RemoteCommandServer)
    selected = Instance(RemoteCommandServer)
    repeater = Instance(CommandRepeater)

    repeaters = List(Instance(CommandRepeater))
    directory_server = Instance(DirectoryServer, ())
    def _check_connection(self):
        for ri in self.repeaters:
            if ri:
                ri.test_connection(verbose=False)

    @on_trait_change('servers[]')
    def _servers_changed(self):
        self.repeaters = [si.repeater for si in self.servers]

    def _selected_changed(self):
        if self.selected:
            self.repeater = self.selected.repeater

    def load(self):
        '''
        '''
        names, de, dh, dp, dr = self.read_configuration()
        if names:
            for s in names:
                e = RemoteCommandServer(name=s,
                               configuration_dir_name='servers',
                               )

                e.bootstrap()
                self.servers.append(e)
        if de:
            self.directory_server.host = dh
            self.directory_server.port = dp
            self.directory_server.root = dr
            self.directory_server.start()


    def opened(self, ui):
        self.edit_traits(
                 view='display_view',
#                  parent=self.ui.control
                 )

        t = Timer(3000, self._check_connection)
        self._timer = t

    def display_view(self):

        v = View(
                 Item('repeaters',
                 show_label=False,
                 editor=ListEditor(mutable=False, style='custom',
                                  editor=InstanceEditor(view='simple_view'))),
                 style='readonly',
                 title='Connection Status',
                 width=200, height=100,
                 )
        return v

    def read_configuration(self):
        '''
        '''

#        ip = InitializationParser()
#        names = ip.get_servers()
#        return names

        config = ConfigParser.ConfigParser()

        path = os.path.join(paths.setup_dir, 'rhs.cfg')
        config.read(path)

        servernames = [s.strip() for s in self.config_get(config, 'General', 'servers').split(',')]

        use_directory_server = False
        dhost, dport, droot = None, None, None

        section = 'DirectoryServer'
        if config.has_section(section):
            if self.config_get(config, section, 'enabled', cast='boolean'):
                use_directory_server = True
                dhost = self.config_get(config, section, 'host', default='localhost')
                dport = self.config_get(config, section, 'port', cast='int', default=8080)
                droot = self.config_get(config, section, 'root', default='')

        return servernames, use_directory_server, dhost, dport, droot


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
        repeater = Group(Item('repeater', style='custom',
                              show_label=False),
                            show_border=True,

                         label='Repeater')
        v = View(HGroup(
                 VGroup(tservers, repeater),
                 servers
                 ),
                 title='Remote Hardware Server',
                 width=700,
                 height=360,
                 resizable=True,
                 handler=AppHandler
                 )

        return v

#============= EOF ====================================
