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
from traits.api import HasTraits, List, on_trait_change, Any
from traitsui.api import View, TableEditor, UItem
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.canvas.canvas2D.laser_tray_canvas import ImageOverlay
#============= standard library imports ========================
#============= local library imports  ==========================

class ImageOverlayManager(HasTraits):
    canvas = Any
    overlays = List
    def set_canvas(self, canvas):
        ov = [o for o in reversed(canvas.overlays)
                         if isinstance(o, ImageOverlay)]
        self.overlays = ov
        self.canvas = canvas

    def traits_view(self):
        cols = [ObjectColumn(name='name', label='Name', editable=False),
                CheckboxColumn(name='visible', label='Visible'),
                ObjectColumn(name='alpha', label='Opacity', width=200),
                ObjectColumn(name='dirname', label='Directory', editable=False)
                ]
        v = View(UItem('overlays', editor=TableEditor(columns=cols,
                                                      sortable=False
                                                      )))
        return v

    @on_trait_change('overlays:[visible,alpha]')
    def redraw(self, obj, name, old, new):
        self.canvas.request_redraw()

#============= EOF =============================================
