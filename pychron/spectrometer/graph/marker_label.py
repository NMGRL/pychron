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
from chaco.label import Label
from kiva import FILL
from traits.trait_types import Bool, Float, Str
from traits.traits import Property
#============= standard library imports ========================
#============= local library imports  ==========================


class MarkerLabel(Label):
    rotate_angle = 0

    zero_y = 0
    xoffset = 10
    indicator_width = 4
    indicator_height = 10
    visible = Bool(True)
    component_height = 100
    x = Float
    y = Float
    data_y = Float
    vertical = False
    horizontal_line_visible = False
    label_with_intensity = False

    text = Property(depends_on='_text, label_with_intensity')
    _text = Str

    def _set_text(self, text):
        self._text =text

    def _get_text(self):
        if self.label_with_intensity:
            return '{:0.4f}'.format(self.data_y)
        else:
            return self._text

    def draw(self, gc, component_height):
        if not self.text:
            self.text = ''

        if self.bgcolor != "transparent":
            gc.set_fill_color(self.bgcolor_)

        #draw tag border
        with gc:
            if self.vertical:
                self.rotate_angle=90
                width, height = self.get_bounding_box(gc)
                gc.translate_ctm(self.x, self.zero_y_vert-35-height)
            else:
                if self.horizontal_line_visible:
                    self._draw_horizontal_line(gc)

                gc.translate_ctm(self.x+self.xoffset, self.y)
                self._draw_tag_border(gc)

            super(MarkerLabel, self).draw(gc)

        with gc:
            gc.translate_ctm(self.x - self.indicator_width / 2.0, self.zero_y)
            self._draw_index_indicator(gc, component_height)

    def _draw_horizontal_line(self, gc):
        with gc:
            # print self.x, self.y
            gc.set_stroke_color((0,0,0,1))
            gc.set_line_width(2)
            oy = 7 if self.text else 4
            y=self.y+oy
            gc.move_to(0, y)
            gc.line_to(self.x, y)
            gc.stroke_path()

    def _draw_index_indicator(self, gc, component_height):
        # gc.set_fill_color((1, 0, 0, 1))
        w, h = self.indicator_width, self.indicator_height
        gc.draw_rect((0, 0, w, h), FILL)

        gc.draw_rect((0, component_height, w, h), FILL)

    def _draw_tag_border(self, gc):
        gc.set_stroke_color((0, 0, 0, 1))
        gc.set_line_width(2)

        # gc.set_fill_color((1, 1, 1, 1))
        bb_width, bb_height = self.get_bounding_box(gc)

        offset = 2
        xoffset = self.xoffset
        gc.lines([(-xoffset, (bb_height + offset) / 2.0),
                  (0, bb_height + 2 * offset),
                  (bb_width + offset, bb_height + 2 * offset),
                  (bb_width + offset, -offset),
                  (0, -offset),
                  (-xoffset, (bb_height + offset) / 2.0)])

        gc.draw_path()
#============= EOF =============================================
