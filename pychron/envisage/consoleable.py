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
from traits.trait_types import Bool, Instance, Event, Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traits.traits import Color
from pychron.loggable import Loggable
from pychron.pychron_constants import LIGHT_YELLOW


class Consoleable(Loggable):
    use_message_colormapping = Bool
    console_display = Instance('pychron.displays.display.DisplayController')
    console_updated = Event
    console_bgcolor = LIGHT_YELLOW
    console_fontsize = Int(11)
    console_default_color = Color('black')

    def console_bind_preferences(self, prefid):
        from pychron.core.ui.preference_binding import color_bind_preference, bind_preference

        color_bind_preference(self, 'console_bgcolor', '{}.bgcolor'.format(prefid))
        color_bind_preference(self, 'console_default_color', '{}.textcolor'.format(prefid))
        bind_preference(self, 'console_fontsize', '{}.fontsize'.format(prefid))

    def console_set_preferences(self, preferences, prefid):
        from pychron.core.ui.preference_binding import set_preference, color_set_preference

        color_set_preference(preferences, self, 'console_bgcolor', '{}.bg_color'.format(prefid))
        color_set_preference(preferences, self, 'console_default_color', '{}.textcolor'.format(prefid))
        set_preference(preferences, self, 'console_fontsize', '{}.fontsize'.format(prefid), cast=int)

    def warning(self, msg, log=True, color=None, *args, **kw):
        super(Consoleable, self).warning(msg, *args, **kw)

        if color is None:
            color = 'red'

        msg = msg.upper()
        if self.console_display:
            self.console_display.add_text(msg, color=color)

        self.console_updated = '{}|{}'.format(color, msg)

    def heading(self, msg, decorate_chr='*', *args, **kw):
        d = decorate_chr * 7
        msg = '{} {} {}'.format(d, msg, d)
        self.info(msg)

    def info(self, msg, log=True, color=None, *args, **kw):
        if color is None:  # or not self.use_message_colormapping:
            color = self.console_default_color

        if self.console_display:
            self.console_display.add_text(msg, color=color)

        if log:
            super(Consoleable, self).info(msg, *args, **kw)

        self.console_updated = '{}|{}'.format(color, msg)

    def info_marker(self, char='=', color=None):
        if color is None:
            color = self.console_default_color
        if self.console_display:
            self.console_display.add_marker(char, color=color)

    def info_heading(self, msg):
        self.info('')
        self.info_marker('=')
        self.info(msg)
        self.info_marker('=')
        self.info('')

    def _console_display_default(self):
        from pychron.displays.display import DisplayController
        return DisplayController(
            bgcolor=self.console_bgcolor,
            font_size=self.console_fontsize,
            default_color=self.console_default_color,
            max_blocks=100)

# ============= EOF =============================================
