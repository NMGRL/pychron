# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.trait_types import Bool, Instance, Event
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.displays.display import DisplayController
from pychron.loggable import Loggable


class Consoleable(Loggable):
    use_message_colormapping = Bool(True)
    console_display = Instance(DisplayController)
    console_updated = Event
    def warning(self, msg, log=True, color=None, *args, **kw):
        super(Consoleable, self).warning(msg, *args, **kw)

        if color is None:
            color = 'red'

        msg = msg.upper()
        if self.console_display:
            self.console_display.add_text(msg, color=color)

        self.console_updated = '{}|{}'.format(color, msg)

    def info(self, msg, log=True, color=None, *args, **kw):
        if color is None or not self.use_message_colormapping:
            color = 'green'

        if self.console_display:
            self.console_display.add_text(msg, color=color)

        if log:
            super(Consoleable, self).info(msg, *args, **kw)

        self.console_updated = '{}|{}'.format(color, msg)

    def info_marker(self, char='=', color=None):
        if color is None:
            color = 'green'
        if self.console_display:
            self.console_display.add_marker(char, color=color)

    def _console_display_default(self):
        return DisplayController(
            bgcolor='#F7F6D0',
            default_color='limegreen',
            max_blocks=100)
#============= EOF =============================================
