#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Str, Color, Button, Float, Property, Bool
from traitsui.api import View, Item, VGroup, HGroup, \
    Spring, UItem, spring, RangeEditor
#============= standard library imports ========================
from threading import Event
import time
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.ui.custom_label_editor import CustomLabel
from pychron.helpers.timer import Timer

class WaitControl(Loggable):
    page_name = Str('Wait')
    message = Str
    message_color = Color('black')

    high = Float
    wtime = Float(10)
    low_name = Float(1)

    current_time = Float
#     current_time = Property(depends_on='current_time')

    auto_start = Bool(False)
    timer = None
    end_evt = None

    continue_button = Button('Continue')

    _continued = Bool
    _canceled = Bool

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

    def join(self):
        time.sleep(0.25)
        while not self.end_evt.is_set():
            time.sleep(0.05)
        self.debug('Join finished')

    def start(self, block=True, evt=None, wtime=None):
        if self.timer:
            self.timer.stop()
            self.timer.wait_for_completion()

        if evt is None:
            evt = Event()

        if evt:
            evt.clear()
            self.end_evt = evt

        if wtime:
            self.wtime=wtime
            self.reset()

        self.timer = Timer(1000, self._update_time,
                           delay=1000
                           )
        self._continued = False

        if block:
            self.join()

    def stop(self):
        self._end()
        self.debug('wait dialog stopped')
        if self.current_time > 1:
            self.message = 'Stopped'
            self.message_color = 'red'
        self.current_time = 0

    def reset(self):
        self.high = self.wtime
        self.current_time = self.wtime
#===============================================================================
# private
#===============================================================================

    def _continue(self):
        self._continued = True
        self._end()
        self.current_time = 0

    def _end(self):
        self.message = ''

        if self.timer is not None:
            self.timer.Stop()
        if self.end_evt is not None:
            self.end_evt.set()

    def _update_time(self):
        if self.timer and self.timer.isActive():
            self.current_time -= 1

    def _current_time_changed(self):
        if self.current_time <= 0:
            self._end()
            self._canceled = False
#===============================================================================
# handlers
#===============================================================================
    def _continue_button_fired(self):
        self._continue()

    def _high_changed(self, v):
        self.wtime = v
        self.current_time = v

    def traits_view(self):
        v = View(VGroup(
                        CustomLabel('message',
                                    size=14,
                                    weight='bold',
                                    color_name='message_color'
                                    ),
                        HGroup(
                               Spring(width=-5, springy=False),
                               Item('high', label='Set Max. Seconds'),
                               spring, UItem('continue_button')
                               ),
                        HGroup(
                               Spring(width=-5, springy=False),
                               Item('current_time', show_label=False,
                                    editor=RangeEditor(mode='slider',
                                                           low_name='low_name',
                                                           high_name='wtime',
                                                           ))
                               ),
                        ),
               )
        return v
#============= EOF =============================================
