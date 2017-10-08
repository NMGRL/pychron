# ===============================================================================
# Copyright 2011 Jake Ross
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
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Instance
from traitsui.api import View, Item

# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
class CanvasPreviewer(HasTraits):
    '''
        G{classtree}
    '''
    canvas = Instance(ExtractionLineCanvas2D)
    def _canvas_default(self):
        '''
        '''
        return ExtractionLineCanvas2D()
    def traits_view(self):
        '''
        '''
        v = View(Item('canvas', editor=ComponentEditor(),
                      show_label=False))
        return v

if __name__ == '__main__':
    c = CanvasPreviewer()
    c.canvas.bootstrap('/Users/Ross/Desktop/canvas.elc')
    c.configure_traits()
# ============= views ===================================
# ============= EOF ====================================
