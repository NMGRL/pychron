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
from pychron.hardware.core.communicators.communicator import Communicator

try:
    import OpenOPC
except ImportError:
    print('OPC required')


    class OpenOPC:
        @classmethod
        def client(cls):
            return None


class OPCCommunicator(Communicator):
    """
        OPC (OLE for Process Control) communicator.
        http://openopc.sourceforge.net/
    """

    server_name = None

    def open(self, *args, **kw):
        self.debug('opening OPC communicator')

        self.handle = OpenOPC.open_client(self.address)

        if self.handle is not None:
            self.handle.connect(self.server_name)
            self.simulation = False
            return True

    def load(self, config, path, **kw):
        self.set_attribute(config, 'server_name', 'Communications', 'server_name')
        # self.set_attribute(config, 'manufacture_id', 'Communications', 'manufacture_id')
        # self.set_attribute(config, 'model_code', 'Communications', 'model_code')
        # self.set_attribute(config, 'serial_number', 'Communications', 'serial_number')
        # self.set_attribute(config, 'usb_interface_number', 'Communications', 'usb_interface_number', optional=True)
        return True

    # def trigger(self):
    #     self.handle.trigger()

    def ask(self, cmd, *args, **kw):
        """
        if cmd is a tuple assume the `ask` call is to write a value
        if cmd is a str assume the `ask` call is to read the parameter "cmd"

        :param cmd:
        :param args:
        :param kw:
        :return:
        """
        if self.simulation:
            return

        if isinstance(cmd, tuple):
            resp = self.handle.write(cmd)
        else:
            resp = self.handle.read(cmd)

        self.debug('cmd==>{}'.format(resp))
        if resp != 'Error':
            value, quality, t = resp
            return value
        elif resp == 'Success':
            return True

    def tell(self, cmd, *args, **kw):
        if self.simulation:
            return

        self.handle.write(cmd)

# ============= EOF =============================================
