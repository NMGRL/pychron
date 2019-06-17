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
from enable.colors import ColorTrait
from kiva.fonttools import str_to_font
from traits.api import HasTraits

from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas
from pychron.canvas.canvas2D.scene.irradiation_scene import IrradiationScene


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Legend(HasTraits):
    measured_color = ColorTrait('purple')
    loaded_color = ColorTrait('green')

    def draw(self, component, gc):
        r = 6
        gc.set_font(str_to_font('modern 10'))
        with gc:
            gc.translate_ctm(20, component.height-50)

            # monitor
            with gc:
                gc.set_line_width(1)
                gc.set_fill_color((0,0,0))
                gc.arc(0, 30, r, 0, 360)

                x = 0
                y = 30
                gc.move_to(x, y - r)
                gc.line_to(x, y + r)
                gc.stroke_path()

                gc.move_to(x - r, y)
                gc.line_to(x + r, y)
                gc.stroke_path()

            gc.set_text_position(10, 26)
            gc.show_text('Monitor')

            # irradiated
            with gc:
                gc.set_line_width(1)
                gc.set_fill_color(self.loaded_color_)
                gc.arc(0, 16, r, 0, 360)
                gc.fill_path()

            gc.set_text_position(10, 12)
            gc.show_text('Irradiated')

            # measured
            with gc:
                gc.set_line_width(1)
                gc.set_fill_color(self.loaded_color_)
                gc.arc(0, 0, r, 0, 360)
                gc.fill_path()

            with gc:
                gc.set_line_width(2)
                gc.set_stroke_color(self.measured_color_)
                gc.arc(0, 0, r + 1, 0, 360)
                gc.stroke_path()

            gc.set_text_position(10, -5)
            gc.show_text('Measured')


class IrradiationCanvas(LoadingCanvas):
    _scene_klass = IrradiationScene
    editable = False

    def __init__(self, *args, **kw):
        self.legend = Legend()
        super(IrradiationCanvas, self).__init__(*args, **kw)

# ============= EOF =============================================
