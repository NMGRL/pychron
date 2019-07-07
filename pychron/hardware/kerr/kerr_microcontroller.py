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



# =============enthought library imports=======================

# =============standard library imports ========================

# =============local library imports  ==========================
from __future__ import absolute_import
from .kerr_device import KerrDevice
class KerrMicrocontroller(KerrDevice):
    """
        Provides access to a `Kerr Controller board <http://www.jrkerr.com/boards.html>`_.
        Used for controlling stepper motors and servos.
    """
    address = '00'
    def initialize(self, *args, **kw):
        """
        """
        # clear the buffers
        self.info('init microcontroller')
        self.parent.tell('0' * 40, is_hex=True)

        cmd = self._build_command('FF', '0F')
        self.ask(cmd, is_hex=True)

        # addr = self.address
        commands = [('00', '2101FF', 100, 'setting module 1 address'),
                    ('00', '2102FF', 100, 'setting module 2 address'),
                    # ('00', '2103FF', 100, 'setting module 3 address')
                    ]
        self._execute_hex_commands(commands, delay=100)

        # verify number of modules found
        commands = [
                   ('01', '0E', 50, 'no op'),
                   ('02', '0E', 50, 'no op')
                   ]
        self._execute_hex_commands(commands)

#        addr = self.address
        #         cmd = '0E'
        #         for addr in ('01', '02'):
        #             c = self._build_command(addr, cmd)
        # #            print addr, c
        #             status_byte = self.ask(c, is_hex=True,
        #                                     delay=100,
        #                                     nbytes=2,
        #                                     info='get defined status',
        #                                     verbose=True)
        #             # print addr, cmd, status_byte

        return True
