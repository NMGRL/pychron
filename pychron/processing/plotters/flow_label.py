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
from traits.api import Bool
from chaco.data_label import DataLabel
#============= standard library imports ========================
from numpy import max
#============= local library imports  ==========================

class FlowDataLabel(DataLabel):
    """
        this label repositions itself if doesn't fit within the
        its component bounds.


    """
    constrain_x = Bool(True)
    constrain_y = Bool(True)
    # def _draw(self, gc, **kw):
    #     self.font='modern 18'
    #     gc.set_font(self.font)
    #     print 'draw', self.font
    #     super(FlowDataLabel, self)._draw(gc,**kw)

    def overlay(self, component, gc, *args, **kw):

        # face name was getting set to "Helvetica" by reportlab during pdf generation
        # set face_name back to "" to prevent font display issue. see issue #72
        self.font.face_name=''

        super(FlowDataLabel, self).overlay(component, gc, *args, **kw)

    def do_layout(self, **kw):
        DataLabel.do_layout(self, **kw)

        ws, hs = self._cached_line_sizes.T
        if self.constrain_x:
            w = max(ws)
            d = self.component.x2 - (self.x + w + 3 * self.border_padding)
            if d < 0:
                self.x += d

            self.x = max((self.x, 0))
        if self.constrain_y:
            h = max(hs)
            self.y = max((self.y, 0))

            yd = self.component.y2 - h - 2 * self.border_padding - self.line_spacing
            self.y = min((self.y, yd))
#============= EOF =============================================
