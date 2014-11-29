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
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from reportlab.platypus.flowables import Flowable
# ============= standard library imports ========================
# ============= local library imports  ==========================

class ComponentFlowable(Flowable):
    component = None
    fixed_scale = None

    def __init__(self, component=None, bounds=None,
                 fixed_scale=None, hAlign='CENTER'):
        self.fixed_scale = fixed_scale
        self.component = component
        if bounds is None:
            bounds = (500, 500)

        self.component.outer_bounds = bounds
        self.component.do_layout(force=True)
        Flowable.__init__(self)
        if hAlign:
            self.hAlign = hAlign

    def _compute_scale(self, page_width, page_height,
                       width, height):
        scale = self.fixed_scale
        if not scale:
            aspect = float(width) / float(height)

            if aspect >= page_width / page_height:
                # We are limited in width, so use widths to compute the scale
                # factor between pixels to page units.  (We want square pixels,
                # so we re-use this scale for the vertical dimension.)
                scale = float(page_width) / float(width)
            else:
                scale = page_height / height

        self._scale = scale
        return scale

    def wrap(self, aW, aH):
        cw, ch = aW, aH
        if self.component:
            cw, ch = self.component.outer_bounds
            scale = self._compute_scale(aW, aH, cw, ch)

        return cw * scale, ch * scale

    def draw(self):
        if self.component:
            gc = PdfPlotGraphicsContext(pdf_canvas=self.canv)

            #             print self.component.x, self.component.y
            scale = self._scale
            gc.scale_ctm(scale, scale)
            gc.translate_ctm(-self.component.x, -self.component.y)
            self.component.draw(gc)

# ============= EOF =============================================
