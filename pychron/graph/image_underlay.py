# ===============================================================================
# Copyright 2012 Jake Ross
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
# ============= standard library imports ========================
import Image
from numpy import array
# ============= local library imports  ==========================

class ImageUnderlay(AbstractOverlay):
    _cached_img = None
    def __init__(self, component, path=None, *args, **kw):
        if path is not None:
            if hasattr(path, 'seek'):
                # if path is a stringio seek back to the beginning
                path.seek(0)
            try:
                im = Image.open(path)
                im = im.convert('RGB')
                self._cached_img = array(im)
            except IOError, e:
                print 'exception', e


        super(ImageUnderlay, self).__init__(component, *args, **kw)

    def overlay(self, component, gc, view_bounds, mode):
        with gc:
            if self._cached_img is not None:
                _x, _y, w, h = view_bounds
                padding = self.padding
                xoff = padding[0] + padding[1]
                yoff = padding[2] + padding[3]
                ch, cw, _ = self._cached_img.shape
#                sw = (component.width) / float(w)
#                sh = (component.height) / float(h)
#                print sw, sh
#                sw, sh = 0.5, 0.5
                sw, sh = float(w - xoff) / float(cw), float(h - yoff) / float(ch)
#                print sw, sh
                gc.scale_ctm(sw, sh)
                gc.draw_image(self._cached_img)

# ============= EOF =============================================
