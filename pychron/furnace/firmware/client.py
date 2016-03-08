# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================
import json
import time
from pyface.message_dialog import warning
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Button
from traitsui.api import View, UItem, Item, HGroup, VGroup, TextEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator, MessageFrame
from pychron.hardware.furnace.nmgrl.camera import NMGRLCamera


class FirmwareClient(HasTraits):
    command = Str  # (enter_set=True, auto_set=False)
    responses = Str

    send_button = Button('Send')

    host = Str
    port = Int

    test_button = Button('Test')
    _cnt = 0

    def __init__(self, *args, **kw):
        super(FirmwareClient, self).__init__(*args, **kw)

        c = EthernetCommunicator(host=self.host, port=self.port,
                                 use_end=True,
                                 kind='TCP')
        self._comm = c

    def test_connection(self):
        if not self._comm.open():
            warning(None, 'Could not connect to {}:{}'.format(self.host, self.port))
        else:
            return True

    def _send(self, cmd):
        resp = self._comm.ask(cmd)
        resp = '{} ==> {}'.format(cmd, resp)
        self.responses = '{}\n{}'.format(self.responses, resp)

    # handlers
    def _test_button_fired(self):
        # if self._cnt % 2 == 0:
        #     self._send('Open FF')
        #     action = 'open'
        # else:
        #     self._send('Close FF')
        #     action = 'close'
        #
        # time.sleep(0.5)
        # self._send('GetIndicatorState FF,{}'.format(action))
        # self._cnt += 1
        # d = json.dumps({'command': 'GetPosition', 'drive': 'feeder', 'position': 1, 'units': 'turns'})
        # d = json.dumps({'command': 'MoveRelative', 'drive': 'feeder', 'position': 1, 'units': 'turns'})
        # v, a, d = self.command.split(',')
        # d = {'command': 'StartJitter', 'drive': 'feeder', 'turns': 0.125, 'p1': 0.1, 'p2': 0.25,
        #      'velocity': int(v), 'acceleration': int(a), 'deceleration': int(d)}
        # d = json.dumps(d)
        # self._send(d)
        # time.sleep(5)
        #
        # d = {'command': 'StopJitter', 'drive': 'feeder'}
        # d = json.dumps(d)
        # self._send(d)

        # mf = MessageFrame()
        # mf.nmessage_len = 8
        # mf.message_len = True
        # imgstr = self._comm.ask('GetImageArray', message_frame=mf, timeout=5)
        # print len(imgstr)
        c = NMGRLCamera()
        print c.get_image_data()

        # resp = self._comm.ask('GetImageArray')
        # print resp
        # print self._send('GetImageArray')

        # for i in range(5):
        #     if i % 2 == 0:
        #         self._send('Open A')
        #     else:
        #         self._send('Close A')
        #     time.sleep(1)

    def _send_button_fired(self):
        self._send(self.command)

    # def _command_changed(self):
    #     self._send(self.command)

    def traits_view(self):
        v = View(VGroup(HGroup(Item('command'), UItem('send_button'), UItem('test_button')),
                        UItem('responses', style='custom',
                              editor=TextEditor(read_only=True))),
                 title='Furnace Firmware Client',
                 resizable=True)
        return v


if __name__ == '__main__':
    c = FirmwareClient(host='192.168.2.2', port=4568)
    # if c.test_connection():
    c.configure_traits()
# ============= EOF =============================================
