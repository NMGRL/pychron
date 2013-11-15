#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Button, String
from traitsui.api import View, Item, ButtonEditor, HGroup
from enable.component_editor import ComponentEditor
from pychron.media_server.image_viewer import ImageViewer
from chaco.abstract_overlay import AbstractOverlay
#============= standard library imports ========================
from numpy import loadtxt
import os
from pychron.geometry.reference_point import ReferencePoint
from pychron.media_server.browser import ReferencePointsTool, ReferencePointsOverlay
from pychron.geometry.affine import calculate_rigid_transform, AffineTransform
#============= local library imports  ==========================
'''
    open a bse image
    
    display analysis points
        -open points file
        -draw point at calibrated xy
    
    
'''


class PointOverlay(AbstractOverlay):
    _cached_points = None
    points = None
    def do_layout(self):
        self._cached_points = None
#
    def overlay(self, component, gc, *args, **w):
        with gc:
            comp = self.component
            if self._cached_points is None:
                self._cached_points = comp.map_screen(self.points)

            r = 4
            for x, y in self._cached_points:
                gc.arc(x, y, r, 0, 360)
                gc.draw_path()


class UVAnalysisImage(ImageViewer):
    open_button = Button
    define_points = Button
    define_points_label = String
    _defining_points = False
#===============================================================================
# handlers
#===============================================================================

    def _set_reference_point(self, pt):
        '''
             assumes no rotation of the reference frames
             only scale and translate
        '''
        rp = ReferencePoint(pt)
        info = rp.edit_traits()
        if info.result:
            plot = self.plot
            self.points.append(((rp.x, rp.y), pt))


#            if not self.reference_pt1:
#                self.reference_pt1 = (rp.x, rp.y), pt
#            else:
#                # calculate bounds
#                dp1, sp1 = self.reference_pt1
#                dp2, sp2 = (rp.x, rp.y), pt
#
#
#                w = plot.width
#                h = plot.height
#                if sp1[0] < sp2[0]:
#                    sx1, sx2 = sp1[0], sp2[0]
#                    x1, x2 = dp1[0], dp2[0]
#                else:
#                    sx2, sx1 = sp1[0], sp2[0]
#                    x2, x1 = dp1[0], dp2[0]
#
#                if sp1[1] < sp2[1]:
#                    sy1, sy2 = sp1[1], sp2[1]
#                    y1, y2 = dp1[1], dp2[1]
#                else:
#                    sy2, sy1 = sp1[1], sp2[1]
#                    y2, y1 = dp1[1], dp2[1]
#
#                pxperunit = abs((sx2 - sx1) / (x2 - x1))
#
#                li = x1 - sx1 / pxperunit
#                hi = x2 + (w - sx2) / pxperunit
#                lv = y1 - sy1 / pxperunit
#                hv = y2 + (h - sy2) / pxperunit
#
#                plot.index_range.low_setting = li
#                plot.index_range.high_setting = hi
#                plot.value_range.low_setting = lv
#                plot.value_range.high_setting = hv
#
            plot.request_redraw()


    def _define_points_fired(self):
        if self.plot:
            plot = self.plot
            if not self._defining_points:
                self.points = []
                st = ReferencePointsTool(plot)
                st.on_trait_change(self._set_reference_point, 'current_position')
                self.points_tool = st
                plot.tools.insert(0, st)
                self.define_points_label = 'Finish'
                plot.overlays.append(ReferencePointsOverlay(tool=st, component=plot))


            else:
                self.define_points_label = 'Define Points'
                self.points_tool.on_trait_change(self._set_reference_point, 'current_position', remove=True)
                plot.tools.pop(0)
                plot.overlays.pop(-1)
                self._calculate_affine_transform(self.points)

            self._defining_points = not self._defining_points

    def load_points(self, path):
        points = [(100, 100),
                  (300, 400),
                  (200, 300)
                  ]

        if os.path.isfile(path):
            points = loadtxt(path, delimiter=',')


        po = PointOverlay(component=self.plot,
                          points=points
                          )
        self.plot.overlays.append(po)

    def _calculate_affine_transform(self, pts):
        rps, ps = zip(*pts)
        s, r, t = calculate_rigid_transform(rps, ps)
        self.A = AffineTransform()
        self.A.scale(s, s)
        self.A.rotate(r)
        self.A.translate(-t[0], -t[1])

        print self.A

    def traits_view(self):
        image = Item('container', style='custom', show_label=False,
                     editor=ComponentEditor()
                     )
        v = View(

                 Item('open_button', show_label=False),
                 Item('define_points',
                      enabled_when='plot',
                      editor=ButtonEditor(label_value='define_points_label'),
                      show_label=False),
                 image,
                 resizable=True
                 )
        return v


if __name__ == '__main__':
    uv = UVAnalysisImage()
    p = '/Users/ross/Sandbox/square array-03_1_SE_1.tif'
    uv.load_image(p)
    p = '/Users/ross/Sandbox/square array-03_1_SE_1.pts'
    uv.load_points(p)
    uv.configure_traits()

#============= EOF =============================================
