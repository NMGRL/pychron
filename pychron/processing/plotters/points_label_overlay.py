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

#============= enthought library imports =======================
from chaco.abstract_overlay import AbstractOverlay
from kiva.fonttools import str_to_font
from traits.api import cached_property, Property, Str, Bool

#============= standard library imports ========================
#============= local library imports  ==========================
class PointsLabelOverlay(AbstractOverlay):
    font = Str('modern 10')
    gfont = Property(depends_on='font')
    #     font = str_to_font('modern 14')

    width = 0
    height = 0

    label_box = Bool(False)

    @cached_property
    def _get_gfont(self):
        return str_to_font(self.font)

    def overlay(self, oc, gc, view_bounds=None, mode="normal"):
        xoffset, yoffset = 10, 0
        with gc:
            gc.clip_to_rect(oc.x, oc.y, oc.x2, oc.y2)

            dd = self.component.index.get_data()
            xs = self.component.index_mapper.map_screen(dd)
            xs += xoffset

            dd = self.component.value.get_data()
            ys = self.component.value_mapper.map_screen(dd)

            gc.set_font(self.gfont)
            w, h, _, _ = gc.get_full_text_extent('ff')
            ys += yoffset - h / 2.0

            show_bound_box = self.label_box
            for xi, yi, li in zip(xs, ys, self.labels):
                with gc:
                    w, h, _, _ = gc.get_full_text_extent(li)
                    if xi + w + 4 > oc.x2:
                        xi -= (xi + w + 4) - oc.x2

                    gc.translate_ctm(xi, yi + 8)
                    if show_bound_box:
                        gc.set_fill_color((1, 1, 1))
                        # gc.set_fill_color((1,))
                        gc.rect(-2, -2, w + 4, h + 4)
                        gc.draw_path()

                    # gc.set_text_position(xi, yi)
                    gc.set_fill_color((0, 0, 0))
                    gc.set_text_position(0, 0)
                    gc.show_text(li)


# ============= EOF =============================================

