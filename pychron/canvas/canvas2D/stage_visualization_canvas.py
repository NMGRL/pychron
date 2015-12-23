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
from traits.api import List, on_trait_change
# from enable.abstract_overlay import AbstractOverlay
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from pychron.core.helpers.iterfuncs import partition


class HoleOverlay(AbstractOverlay):
    holes = List
    results = List

    _cached_pts = None
    _cached_result_pts = None

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):

        if self._cached_pts is None or self._layout_needed:
            self._calculate_cached_points(other_component)

        if self._cached_result_pts is None or self._layout_needed:
            self._calculate_cached_result_points(other_component)

        with gc:
            gc.clip_to_rect(other_component.x, other_component.y,
                            other_component.width, other_component.height)
            with gc:

                for (x, y), r in self._cached_pts:
                    gc.arc(x, y, r, 0, 360)

                gc.stroke_path()

            with gc:

                for pts, color in self._cached_result_pts:
                    gc.set_fill_color(color)
                    gc.set_stroke_color(color)
                    for x, y in pts:
                        gc.arc(x, y, 1, 0, 360)
                    gc.draw_path()

    # private
    def _calculate_cached_result_points(self, comp):
        choles, fholes = partition(self.results, lambda r: r[1])

        cpts = comp.map_screen([(x, y) for (x, y), _ in choles])
        fpts = comp.map_screen([(x, y) for (x, y), _ in fholes])
        self._cached_result_pts = (cpts, (0, 0, 0)), (fpts, (1, 0, 0))

    def _calculate_cached_points(self, comp):
        holes = self.holes
        comp = self.component
        pts = comp.map_screen([(x, y) for (x, y), _ in holes])

        cx, cy = comp.map_screen([(0, 0)])[0]
        rs = comp.map_screen([(d / 2., 0) for _, d in holes])

        rs = map(lambda a: (a[0] - cx), rs)
        pts = zip(pts, rs)
        self._cached_pts = pts

    @on_trait_change('component.+')
    def _handle_component_change(self, name, new):
        self._layout_needed = True
        self.request_redraw()


class StageVisualizationCanvas(BaseDataCanvas):
    aspect_ratio = 1.0

    def build_map(self, sm, results, calibration=None):

        cpos = 0, 0
        rot = 0
        if calibration is not None:
            cpos = calibration.center
            rot = calibration.rotation

        xmi = 100
        xma = -100
        ymi = 100
        yma = -100

        holes = []
        for si in sm.sample_holes:
            x, y = sm.map_to_calibration(si.nominal_position,
                                         cpos, rot)
            xmi = min(x, xmi)
            xma = max(x, xma)
            ymi = min(y, ymi)
            yma = max(y, yma)

            holes.append(((x, y), si.dimension))

        o = HoleOverlay(component=self,
                        holes=holes,
                        results=results)
        self.overlays.append(o)

        pa = 0
        if si is not None:
            pa = si.dimension

        self.set_mapper_limits('x', (xmi, xma), pad=pa)
        self.set_mapper_limits('y', (ymi, yma), pad=pa)
        # self.invalidate_and_redraw()

# def map_dimension(self, d):
#        (w, h), (ox, oy) = self.map_screen([(d, d), (0, 0)])
#        w, h = w - ox, h - oy
#        return w
#     def record_uncorrected(self, h):
#         if isinstance(h, (str, int)):
#             hid = h
#         else:
#             hid = h.id
#
#         cont = self.markupcontainer
#         hole = cont[hid]
#         hole.default_color = (1, 0, 0)
#
#         self.request_redraw()
#
#     def record_correction(self, h, x, y):
#         if isinstance(h, (str, int)):
#             hid = h
#         else:
#             hid = h.id
#
#         name = '{}_cor'.format(hid)
#         cont = self.markupcontainer
#         cont[(name, 2)] = Indicator(x, y,
#                                          canvas=self,
#                                          visible=False
#                                          )
#         ho = cont[hid]
#         ho.default_color = (1, 1, 0)
#         self.request_redraw()
#
#     def record_path(self, p1, p2, name):
#         self.markupcontainer[(name, 2)] = Line(p1, p2, canvas=self)
#         self.request_redraw()
#
#     def record_interpolation(self, hole, x, y, color):
#         cont = self.markupcontainer
#
#         h = cont[hole.id]
#         h.default_color = (0, 0.25, 1)
#         for i, ih in enumerate(hole.interpolation_holes):
#             n = '{}-interpolation-line-{}'.format(hole.id, i)
#             cont[(n, 2)] = Line((x, y), (ih.x_cor, ih.y_cor),
#                                                 canvas=self,
#                                                 visible=False,
#                                                 default_color=(0, 0, 0)
#                                                 )
#         indklass = Indicator
# #        indklass = Circle
#         cont[('{}-interpolation-indicator'.format(hole.id), 3)] = indklass(x, y, canvas=self,
#                                                                                                 default_color=color,
# #                                                                                                radius=hole.dimension / 2.0,
#                                                                                                 visible=False
#                                                                                                 )
#     def set_current_hole(self, h):
#
#         if isinstance(h, (str, int)):
#             hid = h
#         else:
#             hid = h.id
#
#         if self._prev_current:
#             p = self.markupcontainer[self._prev_current]
#             p.state = False
#
#         self.markupcontainer[hid].state = True
#         self._prev_current = hid
#
#     def _selection_hook(self, obj):
#         cont = self.markupcontainer
#
#         cor = cont['{}_cor'.format(obj.name)]
#         if cor is not None:
#             cor.visible = not cor.visible
#
#         # toggle the visiblity of the objects interpolation holes
#         for k, v in cont.iteritems():
#             if k.startswith('{}-interpolation-line'.format(obj.name)):
#                 v.visible = not v.visible
#             elif k == '{}-interpolation-indicator'.format(obj.name):
#                 v.visible = not v.visible
#
#         ihs = obj.hole.interpolation_holes
#         if ihs:
#             for ih in set(ihs):
#                 ihid = ih.id
#                 na = '{}_cor'.format(ihid)
#                 nb = '{}-interpolation-indicator'.format(ihid)
#                 if na in cont:
#                     c = cont[na]
#                 elif nb in cont:
#                     c = cont[nb]
#
#                 c.visible = not c.visible

# ============= EOF =============================================
