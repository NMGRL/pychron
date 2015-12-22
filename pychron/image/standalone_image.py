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
from traits.api import Array, Event, Range
from traitsui.api import UItem, Item, VGroup
# ============= standard library imports ========================
import Image
from numpy import asarray, array, ndarray
# ============= local library imports  ==========================
from pychron.viewable import Viewable
from pychron.core.ui.image_editor import ImageEditor


class StandAloneImage(Viewable):
    source_frame = Array
    refresh = Event
    alpha = Range(0.0, 1.0)
    overlays = None

    def traits_view(self):
        v = self.view_factory(VGroup(Item('alpha'),
                                     UItem('source_frame',
                                           editor=ImageEditor(
                                                   refresh='refresh'))))
        return v

    def load(self, frame, swap_rb=False):
        self.source_frame = array(frame)

    def set_frame(self, frame):
        if not isinstance(frame, ndarray):
            frame = asarray(frame)

        self.overlays = None
        self.source_frame = frame

    def overlay(self, frame, alpha):
        im0 = Image.fromarray(self.source_frame)
        im1 = Image.fromarray(frame)

        self.overlays = (im0, im1)
        self.alpha = alpha

    def _overlay(self, im0, im1, alpha):
        arr = Image.blend(im1, im0, alpha)
        self.source_frame = asarray(arr)

    def _alpha_changed(self):
        if self.overlays:
            im0, im1 = self.overlays
            self._overlay(im0, im1, self.alpha)

# ============= EOF =============================================
