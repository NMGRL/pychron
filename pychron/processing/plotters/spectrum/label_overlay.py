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
from chaco.abstract_overlay import AbstractOverlay
from chaco.plot_label import PlotLabel
from traits.api import List, Bool, Int, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================

class IntegratedPlotLabel(PlotLabel):
    relative_position=Int
    def _draw_overlay(self, gc, view_bounds=None, mode="normal"):
        """ Draws the overlay layer of a component.

        Overrides PlotComponent.
        """
        # Perform justification and compute the correct offsets for
        # the label position
        width, height = self._label.get_bounding_box(gc)
        if self.hjustify == "left":
            x_offset = 0
        elif self.hjustify == "right":
            x_offset = self.width - width
        elif self.hjustify == "center":
            x_offset = int((self.width - width) / 2)
        #
        if self.vjustify == "bottom":
            y=self.component.y+5+(self.relative_position*(height+2))
        elif self.vjustify == "top":
            y = self.component.y2 -height-(self.relative_position*(height+2))

        # elif self.vjustify == "center":
        #     y_offset = int((self.height - height) / 2)
        # x_offset, y_offset=0,0
        # print self.x, self.y, self.width, self.height, self.bounds
        with gc:
            # XXX: Uncomment this after we fix kiva GL backend's clip stack
            #gc.clip_to_rect(self.x, self.y, self.width, self.height)

            # We have to translate to our position because the label
            # tries to draw at (0,0).

            gc.translate_ctm(self.x + x_offset, y)
            self._label.draw(gc)

        return


class SpectrumLabelOverlay(AbstractOverlay):
    display_extract_value=Bool(True)
    display_step=Bool(True)
    nsigma=Int
    font_size=Int
    _cached_labels=List
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        labels=self._get_labels()
        for label in labels:
            label.overlay(other_component, gc)

    def _get_labels(self):
        if self.layout_needed or not self._cached_labels:
            labels=[]
            nsigma=self.nsigma
            spec=self.spectrum
            comp=self.component
            xs = comp.index.get_data()
            ys = comp.value.get_data()
            es=comp.errors
            n=len(xs)
            xs = xs.reshape(n / 2, 2)
            ys = ys.reshape(n / 2, 2)
            es = es.reshape(n / 2, 2)

            for i, ((xa, xb), (ya, yb), (ea, eb)) in enumerate(zip(xs, ys, es)):
                ui=spec.sorted_analyses[i]

                x=(xb-xa)/2.0+xa
                yi,ei=ya,ea
                yl=yi-ei*nsigma
                yu=yi+ei*nsigma

                (x, yl), (_,yu)=comp.map_screen([(x, yl), (x,yu)])
                y=yl-10
                if y<0:
                    y=yu+10
                    if y>comp.height:
                        y=50

                txt=self._assemble_text(ui)
                labels.append(PlotLabel(text=txt,
                                        font='modern {}'.format(self.font_size),
                                        x=x,
                                        y=y))

            self._cached_labels=labels

        return self._cached_labels

    def _assemble_text(self, ai):
        ts=[]
        if self.display_step:
            ts.append(ai.step)

        if self.display_extract_value:
            ts.append(str(ai.extract_value))

        return ' '.join(ts)

    @on_trait_change('display_extract_value, display_step')
    def _update_visible(self):
        self.visible =self.display_extract_value or self.display_step


# ============= EOF =============================================

