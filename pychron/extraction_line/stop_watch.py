# ===============================================================================
# Copyright 2013 Jake Ross
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

import time
from pyface.timer.timer import Timer
from traits.api import HasTraits, Button, Int, Bool, Property
from traitsui.api import Handler, View, Item, UItem, VGroup, HGroup, spring, Spring, ButtonEditor

from pychron.core.ui.lcd_editor import LCDEditor

try:
    from AppKit import NSSpeechSynthesizer

    SPEECHSYNTH = NSSpeechSynthesizer.alloc().initWithVoice_("com.apple.speech.synthesis.voice.Vicki")
    SPEECHSYNTH.setRate_(275)
except ImportError:
    SPEECHSYNTH = None


class StopWatchHandler(Handler):
    def closed(self, info, isok):
        info.object.destroy()


class StopWatch(HasTraits):
    start_stop_button = Button
    reset_button = Button('Reset')
    current_time = Int
    call_interval = Int(5)
    _alive = Bool

    start_stop_label = Property(depends_on='_alive')
    _base_time = 0

    def destroy(self):
        if self._timer:
            self._timer.Stop()

    def _iter(self):
        elapsed = int(round(time.time() - self._start_time))
        self.current_time = self._base_time + elapsed

        if self.call_interval and not self.current_time % self.call_interval:
            if SPEECHSYNTH:
                SPEECHSYNTH.startSpeakingString_(str(self.current_time))

    def _reset_button_fired(self):
        self.current_time = 0
        self._base_time = 0

    def _start_stop_button_fired(self):
        if self._alive:
            self._timer.Stop()
            self._base_time = self.current_time
        else:
            self._start_time = time.time()

            t = Timer(1000, self._iter)
            self._timer = t

        self._alive = not self._alive

    def traits_view(self):
        v = View(VGroup(UItem('current_time', editor=LCDEditor()),
                 HGroup(UItem('start_stop_button', editor=ButtonEditor(label_value='start_stop_label')),
                        UItem('reset_button', enabled_when='not _alive'),spring, Item('call_interval'))),
                 handler=StopWatchHandler,
                 title='StopWatch')
        return v

    def _get_start_stop_label(self):
        return 'Stop' if self._alive else 'Start'


if __name__ == '__main__':
    s = StopWatch()
    s.configure_traits()


# ============= EOF =============================================
