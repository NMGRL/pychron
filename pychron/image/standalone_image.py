# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Array, Event
from traitsui.api import View, UItem
# ============= standard library imports ========================
from numpy import asarray, array, ndarray
# ============= local library imports  ==========================
from pychron.viewable import Viewable
from pychron.core.ui.image_editor import ImageEditor


class StandAloneImage(Viewable):
    source_frame = Array
    refresh = Event

    def traits_view(self):
        v = View(UItem('source_frame',
                       editor=ImageEditor(refresh='refresh')),
                 width=self.window_height,
                 height=self.window_width,
                 x=self.window_x, y=self.window_y)
        return v

    def load(self, frame, swap_rb=False):
        self.source_frame = array(frame)

    def set_frame(self, frame):
        if not isinstance(frame, ndarray):
            frame = asarray(frame)

        self.source_frame = frame

# ============= EOF =============================================
