# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
import time

from traits.api import Property, provides

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.actuators.iactuator import IActuator
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


@provides(IActuator)
class ApisController(CoreDevice):
    connection_url = Property

    # close `isolation_valve` `isolation_delay` seconds after loading of pipette started
    isolation_delay = 25
    # name of valve to make analytical section static
    isolation_valve = 'U'
    isolation_info = 'isolate microbone'

    # instead of the simple wait/close sequence use the a gosub
    # use this for a more complex/flexible pattern i.e open/close multiple valves
    isolation_gosub = None

    def load_additional_args(self, config):
        v = self.config_get(config, 'Isolation', 'valve', optional=False, default='U')
        self.isolation_delay = self.config_get(config, 'Isolation', 'delay', optional=False, cast='int', default=25)
        self.isolation_info = self.config_get(config, 'Isolation', 'info', optional=True)
        self.isolation_gosub = self.config_get(config, 'Isolation', 'gosub', optional=True)

        self.isolation_valve = v.replace('"', '').replace("'", '')

        return True

    #iacuator protocol
    def close_channel(self, obj):
        self.set_external_pumping(False)
        return True

    def open_channel(self, obj):
        self.set_external_pumping(True)
        return True

    def get_channel_state(self, obj):
        pass

    def get_lock_state(self, obj):
        pass

    def script_loading_block(self, script, **kw):
        """
            wait for script loading to complete.

            this process has three steps.
            1. wait for loading to start. status changes from 1 to 2

            2. if isolation_gosub
                  do gosub
               else
                  wait `isolation_delay` seconds then close the `isolation valve`

            3. wait for apis script to complete

            return True if completed successfully
        """
        script.console_info('waiting for pipette to load')
        if not self.blocking_poll('loading_started', script=script, **kw):
            return
        script.console_info('loading started')

        if self.isolation_gosub:
            self.debug('executing isolation gosub= {}'.format(self.isolation_gosub))
            script.gosub(self.isolation_gosub)
        else:
            ws = self.isolation_delay
            self.debug('wait {}s'.format(ws))
            time.sleep(ws)

            if self.isolation_info:
                script.console_info(self.isolation_info)

            iv = self.isolation_valve
            iv=iv.split(',')

            for v in iv:
                script.close(v.strip())

        script.console_info('wait for apis to complete expansion')
        return self.blocking_poll('get_loading_complete', script=script, **kw)

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

    def get_status(self):
        cmd = self.make_command('status')
        status = self.ask(cmd)
        return status

    def get_loading_status(self):
        status = self.get_status()
        try:
            status = STATUS_MAP[status]
            return status
        except KeyError:
            pass

    def loading_started(self):
        status = self.get_loading_status()
        return status == 'Loading pipette'

    def get_loading_complete(self):
        status = self.get_loading_status()
        return status == 'Expansion complete'

    def get_available_blanks(self):
        cmd = self.make_command('list_blanks')
        return self.ask(cmd)

    def get_available_airs(self):
        cmd = self.make_command('list_airs')
        return self.ask(cmd)

    def set_external_pumping(self, state):
        cmd = self.make_command('set_external_pumping')
        cmd = '{},{}'.format(cmd, 'true' if state else 'false')
        return self.ask(cmd)

    def _get_connection_url(self):
        return '{}:{}'.format(self.communicator.host, self.communicator.port)

# ============= EOF =============================================

