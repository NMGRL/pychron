#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Property
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice

CMD_MAP = {'list_blanks': '100',
           'list_airs': '101',
           'last_runid': '102',
           'pipette_record': '103',
           'status': '104',
           'load_blank': '105',
           'load_air': '106',
           'cancel': '107',
           'set_external_pumping': '108'}

STATUS_MAP = {'0': 'Idle',
              '1': 'Pumping pipette',
              '2': 'Loading pipette',
              '3': 'Expanding pipettes',
              '4': 'Expansion complete'}


class ApisController(CoreDevice):
    connection_url = Property

    def _get_connection_url(self):
        return '{}:{}'.format(self._communicator.host, self._communicator.port)

    def make_command(self, cmd):
        try:
            return CMD_MAP[cmd]
        except KeyError:
            return 'invalid command cmd={}'.format(cmd)

    def load_blank(self, name):
        cmd = self.make_command('load_blank')
        self.ask('{},{}'.format(cmd, name))

    def load_pipette(self, name):
        cmd = self.make_command('load_air')
        self.ask('{},{}'.format(cmd, name))

    def get_loading_status(self):
        cmd = self.make_command('status')
        status = self.ask(cmd)
        try:
            status = STATUS_MAP[status]
            return status
        except KeyError:
            pass

    def get_loading_complete(self):
        status = self.get_loading_status()
        return status == 'Expansion complete'

    def get_available_blanks(self):
        cmd = self.make_command('list_blanks')
        return self.ask(cmd)

    def get_available_airs(self):
        cmd = self.make_command('list_airs')
        return self.ask(cmd)

#============= EOF =============================================

