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

# ============= standard library imports ========================
import time
from threading import Event

# ============= enthought library imports =======================
from traits.api import Str, Color, Button, Float, Bool, Property, Int, Event as TEvent

# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.timer import Timer
from pychron.loggable import Loggable


class WaitControl(Loggable):
    page_name = Str("Wait")
    message = Str
    message_color = Color("black")

    high = Int(auto_set=False, enter_set=True)
    duration = Float(10)

    current_time = Float
    current_display_time = Property(depends_on="current_time")

    auto_start = Bool(False)
    timer = None
    end_evt = None

    continue_button = Button("Continue")
    pause_button = TEvent
    pause_label = Property(depends_on="_paused")
    _paused = Bool
    _continued = Bool
    _canceled = Bool
    _no_update = False

    def __init__(self, *args, **kw):
        self.reset()
        super(WaitControl, self).__init__(*args, **kw)
        if self.auto_start:
            self.start(evt=self.end_evt)

    def is_active(self):
        if self.timer:
            return self.timer.isActive()

    def is_canceled(self):
        return self._canceled

    def is_continued(self):
        return self._continued

    def join(self, evt=None):
        if evt is None:
            evt = self.end_evt

        if self.duration > 1:
            evt.wait(self.duration - 1)

        while not evt.wait(timeout=0.25):
            pass

        #     time.sleep(0.25)
        # while evt.is_set():
        #     evt.wait(0.5)

        self.debug("Join finished")

    def start(self, block=True, evt=None, duration=None, message=None, paused=False):
        if self.end_evt:
            self.end_evt.set()

        if evt is None:
            evt = Event()

        if evt:
            evt.clear()
            self.end_evt = evt

        if self.timer:
            # stopping and wait for completion seems redundant. Stop sets the flag to false then
            # wait for completion checks if the flag is false or not.
            # will leave for now
            self.timer.stop()
            self.timer.wait_for_completion()

        if duration:
            # self.duration = 1
            self.duration = duration
            self.reset()

        if message:
            self.message = message

        self.timer = Timer(1000, self._update_time, delay=1000)
        # self.timer = Timer()
        self._continued = False
        self._paused = paused

        if block:
            self.join(evt=evt)
            if evt == self.end_evt:
                self.end_evt = None

    def stop(self):
        self._end()
        self.debug("wait dialog stopped")
        if self.current_time > 1:
            self.message = "Stopped"
            self.message_color = "red"
            # self.current_time = 0

    def reset(self):
        with no_update(self, fire_update_needed=False):
            self.high = int(self.duration)
            self.current_time = self.duration
            self._paused = False

    def pause(self):
        self._paused = True

    # ===============================================================================
    # private
    # ===============================================================================

    def _continue(self):
        self._paused = False
        self._continued = True
        self._end()
        self.current_time = 0

    def _end(self):
        self.message = ""

        if self.timer is not None:
            self.timer.Stop()
        if self.end_evt is not None:
            self.end_evt.set()

    def _update_time(self):
        if self._paused:
            return
        ct = self.current_time
        if self.timer and self.timer.isActive():
            self.current_time -= 1
            ct -= 1
            # self.debug('Current Time={}/{}'.format(ct, self.duration))
            if ct <= 0:
                self._end()
                self._canceled = False
            else:
                self.current_time = ct

                # def _current_time_changed(self):
                # if self.current_time <= 0:
                # self._end()
                # self._canceled = False

    def _get_current_display_time(self):
        return "{:03d}".format(int(self.current_time))

    def _get_pause_label(self):
        return "Unpause" if self._paused else "Pause"

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _pause_button_fired(self):
        print("asdfas", self._paused)
        self._paused = not self._paused

    def _continue_button_fired(self):
        self._continue()

    def _high_changed(self, v):
        if self._no_update:
            return

        self.duration = v
        self.current_time = v

        # def traits_view(self):
        # v = View(VGroup(
        #         CustomLabel('message',
        #                     size=14,
        #                     weight='bold',
        #                     color_name='message_color'),
        #
        #         HGroup(Spring(width=-5, springy=False),
        #                Item('high', label='Set Max. Seconds'),
        #                spring, UItem('continue_button')),
        #         HGroup(Spring(width=-5, springy=False),
        #                Item('current_time', show_label=False,
        #                     editor=RangeEditor(mode='slider',
        #                                        low=1,
        #                                        # low_name='low_name',
        #                                        high_name='duration')),
        #                CustomLabel('current_time',
        #                            size=14,
        #                            weight='bold'))))
        #     return v


# ============= EOF =============================================
