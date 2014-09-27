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
from chaco.abstract_overlay import AbstractOverlay
from traits.has_traits import on_trait_change
from traits.trait_types import List
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.spectrometer.graph.marker_label import MarkerLabel


class MarkerOverlay(AbstractOverlay):
    labels = List
    _cached_labels = List
    indicator_height = 10

    @on_trait_change('_cached_labels:[text, visible]')
    def _handle_text_change(self):
        self.request_redraw()

    def add_marker(self, x, y, text, bgcolor='white'):
        m = MarkerLabel(data_x=self.component.index_mapper.map_data(x),
                        indicator_height=self.indicator_height,
                        zero_y=self.component.y - self.indicator_height / 2.0,
                        bgcolor=bgcolor,
                        x=x,
                        y=y, text=text)
        self.labels.append(m)
        self._layout_needed = True
        return m

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(other_component.x, other_component.y - self.indicator_height / 2.0,
                            other_component.width, other_component.height + self.indicator_height)

            # self._load_cached_labels()
            self._draw_labels(gc)

    def _do_layout(self):
        if self._layout_needed:
            mapper = self.component.index_mapper
            self._cached_labels = self.labels[:]
            for ci in self._cached_labels:
                if ci.visible:
                    ci.x = mapper.map_screen(ci.data_x)
                    ci.visible = bool(ci.x > 0)
                    # print ci.data_x, ci.x, mapper.range.low, mapper.range.high
            self._layout_needed = False

    def _draw_labels(self, gc):
        for ci in self._cached_labels:
            if ci.visible:
                with gc:
                    ci.draw(gc, self.component.height)
#============= EOF =============================================
