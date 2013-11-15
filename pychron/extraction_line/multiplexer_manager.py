#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Str, Button
from traitsui.api import Item, HGroup, spring
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.hardware.core.core_device import CoreDevice
from pychron.ui.custom_label_editor import CustomLabel

class HeaderLabel(CustomLabel):
    color = 'maroon'
    size = 14
class MultiplexerManager(Manager):
    controller = Instance(CoreDevice)
    hname = Str('Name')
    haddress = Str('Address')
    hvalue = Str('Value')
    hprocessvalue = Str('ProcessValue')
    title = 'Multiplexer'
    window_width = 500
    window_height = 500
    id = 'multiplexer_manager'
    reload_channels_button = Button('Reload')

    def reload_channels(self):
        self.closed(True)
        self.controller.bootstrap()
        self.controller.post_initialize()
        self.opened(None)

    def opened(self, ui):
        self.controller.start_scan()

    def closed(self, isok):
        self.controller.stop_scan()
        return isok

    def finish_loading(self):
        if self.devices:
            self.controller = self.devices[0]

#===============================================================================
# handlers
#===============================================================================
    def _reload_channels_button_fired(self):
        self.reload_channels()

    def traits_view(self):
        v = self.view_factory(
               HGroup(
#                      CustomLabel('hname', size=18, color='maroon', width=200),
                      HeaderLabel('hname', width=200),
#                      Item('hname', show_label=False, style='readonly', width=200),
                      HeaderLabel('haddress', width=75),

#                      Item('haddress', show_label=False, style='readonly', width=75),
                      HeaderLabel('hvalue', width=100),
#                      Item('hvalue', show_label=False, style='readonly', width=100),
                      HeaderLabel('hprocessvalue', width=100)
#                      Item('hprocessvalue', show_label=False, style='readonly', width=100)
                      ),
               Item('controller', style='custom', show_label=False),
               HGroup(spring, Item('reload_channels_button', show_label=False)),
               )

        return v
#============= EOF =============================================
