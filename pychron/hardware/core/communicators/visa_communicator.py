# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import
from pychron.hardware.core.communicators.communicator import Communicator
from pychron.hardware.core.communicators.visa import resource_manager
from pyvisa.constants import StatusCode

class VisaCommunicator(Communicator):
    """
        uses PyVisa as main interface to USB.
    """
    board = 0
    manufacture_id = 0
    model_code = 0
    serial_number = 0
    usb_interface_number = None

    def _make_address(self):
        base = 'USB{}::{}::{}::{}'.format(self.board, self.manufacture_id, self.model_code, self.serial_number)
        if self.usb_interface_number:
            base = '{}::{}'.format(base, self.usb_interface_number)

        return '{}::INSTR'.format(base)

    def open(self, *args, **kw):
        self.debug('opening visa usb communicator')

        address = self._make_address()
        self.handle = resource_manager.get_instrument(address)
        if self.handle is not None:
            self.simulation = False
            return True

    def load(self, config, path, **kw):
        self.set_attribute(config, 'board', 'Communications', 'board')
        self.set_attribute(config, 'manufacture_id', 'Communications', 'manufacture_id')
        self.set_attribute(config, 'model_code', 'Communications', 'model_code')
        self.set_attribute(config, 'serial_number', 'Communications', 'serial_number')
        self.set_attribute(config, 'usb_interface_number', 'Communications', 'usb_interface_number', optional=True)
        return True

    def trigger(self):
        self.handle.trigger()

    def ask(self, cmd, *args, **kw):
        resp = self.handle.query(cmd)
        self.debug('cmd==>{}'.format(resp))
        return resp

    def tell(self, cmd, *args, **kw):
        self.handle.write(cmd)

# ============= EOF =============================================
