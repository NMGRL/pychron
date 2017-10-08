# ===============================================================================
# Copyright 2016 Jake Ross
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
import os

from PIL import Image
from affine import Affine
from pychron.core.geometry.affine import AffineTransform, calculate_rigid_itransform_affine, calculate_rigid_itransform

from chaco.array_plot_data import ArrayPlotData
from chaco.image_plot import ImagePlot
from chaco.plot import Plot
from chaco.tools.image_inspector_tool import ImageInspectorTool
from enable.base_tool import BaseTool
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Instance, Event, Tuple, Enum
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
from numpy import array
# ============= local library imports  ==========================
from traitsui.handler import Controller

from pychron.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from pychron.core.geometry.affine import calculate_rigid_transform


class RegisteredImageInspectorTool(BaseTool):
    """ A tool that captures the color and underlying values of an image plot.
    """

    # Indicates whether overlays listening to this tool should be visible.
    # visible = Bool(True)

    # Stores the value of self.visible when the mouse leaves the tool,
    # so that it can be restored when the mouse enters again.
    # _old_visible = Enum(None, True, False)  # Trait(None, Bool(True))

    goto_event = Event
    move_event = Event

    # def normal_key_pressed(self, event):
    #     if self.inspector_key.match(event):
    #         self.visible = not self.visible
    #         event.handled = True

    # def normal_mouse_leave(self, event):
    #     if self._old_visible is None:
    #         self._old_visible = self.visible
    #         self.visible = False
    #
    # def normal_mouse_enter(self, event):
    #     if self._old_visible is not None:
    #         self.visible = self._old_visible
    #         self._old_visible = None

    def normal_left_down(self, event):
        if event.shift_down:
            self.goto_event = event.x, event.y

    def normal_mouse_move(self, event):
        self.move_event = event.x, event.y

        #     """ Handles the mouse being moved.
        #
        #     Fires the **new_value** event with the data (if any) from the event's
        #     position.
        #     """
        #     plot = self.component
        #     if plot is not None:
        #         if isinstance(plot, ImagePlot):
        #             ndx = plot.map_index((event.x, event.y))
        #             if ndx == (None, None):
        #                 self.new_value = None
        #                 return
        #
        #             x_index, y_index = ndx
        #             image_data = plot.value
        #
        #             # if hasattr(plot, "_cached_mapped_image") and \
        #             #        plot._cached_mapped_image is not None:
        #             #     self.new_value = \
        #             #             dict(indices=ndx,
        #             #                  data_value=image_data.data[y_index, x_index],
        #             #                  color_value=plot._cached_mapped_image[y_index,
        #             #                                                        x_index])
        #             #
        #             # else:
        #             #     self.new_value = \
        #             #         dict(indices=ndx,
        #             #              color_value=image_data.data[y_index, x_index])
        #
        #             self.last_mouse_position = (event.x, event.y)
        #     return


class RegisteredImage(HasTraits):
    path = Str

    stage_manager = Any
    pd = Instance(ArrayPlotData, ())
    plot = Instance(Plot)
    position = Str

    _image_width = 0
    _image_height = 0

    def __init__(self, *args, **kw):
        super(RegisteredImage, self).__init__(*args, **kw)
        self.plot = plot = Plot(self.pd, default_origin="top left")
        plot.x_axis.orientation = "top"
        plot.x_axis.visible = False
        plot.y_axis.visible = False

    def load_registration(self):

        refpoints = [[375.23, 443.17],
                     [525.42, 183.47],
                     [265.72, 33.39],
                     # [470, 90]
                     ]
        points = [[1, 1],
                  [1, -1],
                  [-1, -1],
                  # [1, 1]
                  ]

        self._load_affine(refpoints, points)

    def load_path(self, path):
        self.path = path

    # private
    def _load_affine(self, refpoints, points):
        af = calculate_rigid_itransform_affine(refpoints, points)
        self.affine = af

    # handlers
    def _path_changed(self, new):
        if new:
            img = Image.open(new)
            self._image_width, self._image_height = float(img.width), float(img.height)
            self.plot.aspect_ratio = self._image_width/self._image_height

            pflag = 'imagedata' not in self.pd.list_data()
            self.pd.set_data('imagedata', array(img))
            if pflag:
                img_plot = self.plot.img_plot('imagedata')[0]
                imgtool = RegisteredImageInspectorTool(img_plot)
                imgtool.on_trait_change(self._handle_move, 'move_event')
                imgtool.on_trait_change(self._handle_goto, 'goto_event')
                img_plot.tools.append(imgtool)

    def _handle_move(self, new):
        if new:
            sx, sy = new

            w, h = self.plot.bounds
            ssx, ssy = self._image_width / w, self._image_height / h
            self.affine.scale(ssx, ssy)
            dx, dy = self.affine.transform(sx, sy)
            self.affine.scale(1 / ssx, 1 / ssy)

            s = 'screen:{},{}'.format(int(sx), int(sy))
            self.position = '{:<20s} data:{:0.3f},{:0.3f}'.format(s, dx, dy)

    def _handle_goto(self, new):
        if new:
            sx, sy = new
            dx, dy = self.affine.transform(sx, sy)
            print 'goto {}, {}'.format(new, (dx, dy))
            self.stage_manager.linear_move(dx, dy)


class RegisteredImageViewer(Controller):
    model = Instance(RegisteredImage)

    def traits_view(self):
        v = View(VGroup(UItem('plot', editor=ComponentEditor(width=740, height=600)),
                        Item('position', style='readonly')),
                 resizable=True)
        return v


if __name__ == '__main__':
    class SM:
        def linear_move(self, dx, dy):
            print 'moving to {}, {}'.format(dx, dy)


    r = RegisteredImage(stage_manager=SM())
    p = '/Users/ross/Programming/registered_image_rotate30.04-01.png'
    r.load_path(p)
    r.load_registration()

    vv = RegisteredImageViewer(model=r)
    vv.configure_traits()
# ============= EOF =============================================
# def r1():
#     refpoints = [[170, 390],
#                  [170, 90],
#                  [470, 390],
#                  # [470, 90]
#                  ]
#     points = [[-1, 1],
#               [-1, -1],
#               [1, 1],
#               # [1, 1]
#               ]
#
#     af = calculate_rigid_itransform_affine(points, refpoints)
#
#     r.affine = af
#     r.path = '/Users/ross/Programming/registered_image.png'
#
#
# def r2():
#     refpoints = [[375.23, 443.17],
#                  [525.42, 183.47],
#                  [265.72, 33.39],
#                  # [470, 90]
#                  ]
#     points = [[1, 1],
#               [1, -1],
#               [-1, -1],
#               # [1, 1]
#               ]
#
#     # scale, theta, tx, ty = calculate_rigid_itransform(refpoints, points)
#     # print 'i',calculate_rigid_itransform(refpoints, points)
#     # print 't',calculate_rigid_transform(refpoints, points)
#     #
#     # a = AffineTransform()
#     # a.translate(tx, ty)
#     # a.rotate(theta)
#     # a.scale(scale, scale)
#     #
#     # print calculate_rigid_itransform(refpoints, points)
#     af = calculate_rigid_itransform_affine(refpoints, points)
#
#     r.affine = af
#     r.path = '/Users/ross/Programming/registered_image_rotate30.04-01.png'
# r2()
# print r.affine.transform(115.53, 292.99)
