#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, TraitType, List, Event
from traitsui.api import View, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.qt.pie_clock_editor import PieClockEditor


class PieClock(TraitType):
    slices = List

    def create_editor(self):
        editor = PieClockEditor(start_event='start_event',
                                stop_event='stop_event',
                                update_slices_event='update_slices_event')
        return editor


class PieClockModel(HasTraits):
    pie_clock = PieClock
    start_event = Event
    stop_event = Event
    update_slices_event = Event

    def traits_view(self):
        v = View(UItem('pie_clock',
                       width=150,
                       height=150))
        return v

    def set_slices(self, slices, colors):
        self.pie_clock.slices = zip(slices, colors)
        self.update_slices_event = True

    def start(self):
        self.start_event = True

    def stop(self):
        self.stop_event = True


#============= EOF =============================================

