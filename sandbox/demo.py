#===============================================================================
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
#===============================================================================
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'
import time

from traits.api import HasTraits, Any, Int, Button, Float, List, Event, \
    Instance
from traitsui.api import View, Item

from pychron.canvas.canvas2D.laser_tray_canvas import LaserTrayCanvas
from pychron.canvas.canvas2D.image_overlay_manager import ImageOverlayManager

from enable.component_editor import ComponentEditor


class Demo(HasTraits):
    canvas = Instance(LaserTrayCanvas, ())
    editor = Instance(ImageOverlayManager, ())

    def traits_view(self):
        v = View(
            Item('canvas',
                 show_label=False,
                 style='custom',
                 editor=ComponentEditor()),

            Item('editor', style='custom', show_label=False),
            resizable=True
        )
        return v

    # from pychron.ui.qt.pie_clock_editor import PieClockEditor
# from pychron.ui.thread import Thread
# class Demo(HasTraits):
#     pie_clock = Float
#     test = Button
# #     slices = List
#     slices = List
#     update_slices = Event
#     def _test_fired(self):
#         t = Thread(target=self._test)
#         t.start()
#         self._t = t
#
#     def _test(self):
# #         slices = (5, 5, 5, 5, 5, 10)
#         slices = [5, 5, 5, 5, 5, 10]
#
#         self.slices = slices
#         self.update_slices = True
# #         self.slices = slices
# #         slices = self.slices
#         total = float(sum(slices))
#
#         for i in range(int(total)):
#             self.pie_clock = 360 / total * i
#             time.sleep(1)
#
#         self.pie_clock = 0
#
#     def traits_view(self):
#         v = View(
#                  Item('test'),
#                  Item('pie_clock',
#                       show_label=False,
#                       editor=PieClockEditor(
#                                             slices='slices',
#                                             update_slices='update_slices'
#                                             ),
#                       width=300,
#                       height=300,
#                     ),
#                  resizable=True
#                 )
#         return v
def setup(d):
    p = '/Users/ross/Sandbox/pos_err/diodefailsnapshot.jpg'

    '''
    add ability to define rigid transform for this image
    table of calibration points
    user can add/delete/edit rows
    
    move laser to calibration point
    record laser x,y (mm) 
    ask user for image x,y (mm)
    
    compute rigid transform
    
    add to calibration types?
    Tray, Free, Image
    
    Image Calibration
    - ask for image to load
    - do a free calibration
    
    
    
    
    '''
    d.canvas.add_image_underlay(p, 0.5)

    p = '/Users/ross/Sandbox/pos_err/pos_err_3_0-002.jpg'
    d.canvas.add_image_underlay(p, 0.7)

    d.editor.set_canvas(d.canvas)


if __name__ == '__main__':
    d = Demo()
    setup(d)
    d.configure_traits()
