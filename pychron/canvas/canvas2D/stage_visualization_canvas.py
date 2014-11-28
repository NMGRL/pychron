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

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.canvas.canvas2D.markup.markup_canvas import MarkupCanvas
from pychron.canvas.canvas2D.scene.primitives.primitives import Circle, Indicator, Line
# from pychron.canvas.canvas2D.markup.markup_items import Circle, Line, PointIndicator, \
#    Indicator

class InfoObject(object):
    pass

class SampleHole(Circle, InfoObject):
    display_interpolation = False
    hole = None
    def _render_(self, gc):
        super(SampleHole, self)._render_(gc)

        gc.save_state()
        x, y = self.get_xy()
        hid = self.hole.id
        w, h, _, _ = gc.get_full_text_extent(hid)
        gc.set_fill_color((0, 0, 0))
        gc.set_text_position(x - w / 2.0, y - h / 2.0)
        gc.show_text(hid)

        gc.restore_state()

class StageVisualizationCanvas(MarkupCanvas):
    _prev_current = None
#    use_zoom = False
#    show_grids=True
    def build_map(self, sm, calibration=None):
#        sm.load_correction_file()

        cpos = 0, 0
        rot = 0
        if calibration is not None:
            cpos = calibration[0]
            rot = calibration[1]

        xmi = 100
        xma = -100
        ymi = 100
        yma = -100
        si = None
        for si in sm.sample_holes:
            x, y = sm.map_to_calibration(si.nominal_position,
                                      cpos, rot)

            xmi = min(x, xmi)
            xma = max(x, xma)
            ymi = min(y, ymi)
            yma = max(y, yma)
            self.markupcontainer[si.id] = SampleHole(x, y, canvas=self,
                                                 default_color=(0, 0, 0),
#                                                fill=True,
                                                name=si.id,
#                                                hole=weakref.ref(si),
                                                hole=si,
                                                radius=si.dimension / 2.0
                                                )

            if si.has_correction():
                self.record_correction(si, si.x_cor, si.y_cor)

        pa = 0
        if si is not None:
            pa = si.dimension
#         self.set_mapper_limits('x', (xmi, xma), pad=si.dimension)
#         self.set_mapper_limits('y', (ymi, yma), pad=si.dimension)
        self.set_mapper_limits('x', (xmi, xma), pad=pa)
        self.set_mapper_limits('y', (ymi, yma), pad=pa)
        self.invalidate_and_redraw()

#    def map_dimension(self, d):
#        (w, h), (ox, oy) = self.map_screen([(d, d), (0, 0)])
#        w, h = w - ox, h - oy
#        return w
    def record_uncorrected(self, h):
        if isinstance(h, (str, int)):
            hid = h
        else:
            hid = h.id

        cont = self.markupcontainer
        hole = cont[hid]
        hole.default_color = (1, 0, 0)

        self.request_redraw()

    def record_correction(self, h, x, y):
        if isinstance(h, (str, int)):
            hid = h
        else:
            hid = h.id

        name = '{}_cor'.format(hid)
        cont = self.markupcontainer
        cont[(name, 2)] = Indicator(x, y,
                                         canvas=self,
                                         visible=False
                                         )
        ho = cont[hid]
        ho.default_color = (1, 1, 0)
        self.request_redraw()

    def record_path(self, p1, p2, name):
        self.markupcontainer[(name, 2)] = Line(p1, p2, canvas=self)
        self.request_redraw()

    def record_interpolation(self, hole, x, y, color):
        cont = self.markupcontainer

        h = cont[hole.id]
        h.default_color = (0, 0.25, 1)
        for i, ih in enumerate(hole.interpolation_holes):
            n = '{}-interpolation-line-{}'.format(hole.id, i)
            cont[(n, 2)] = Line((x, y), (ih.x_cor, ih.y_cor),
                                                canvas=self,
                                                visible=False,
                                                default_color=(0, 0, 0)
                                                )
        indklass = Indicator
#        indklass = Circle
        cont[('{}-interpolation-indicator'.format(hole.id), 3)] = indklass(x, y, canvas=self,
                                                                                                default_color=color,
#                                                                                                radius=hole.dimension / 2.0,
                                                                                                visible=False
                                                                                                )
    def set_current_hole(self, h):

        if isinstance(h, (str, int)):
            hid = h
        else:
            hid = h.id

        if self._prev_current:
            p = self.markupcontainer[self._prev_current]
            p.state = False

        self.markupcontainer[hid].state = True
        self._prev_current = hid

    def _selection_hook(self, obj):
        cont = self.markupcontainer

        cor = cont['{}_cor'.format(obj.name)]
        if cor is not None:
            cor.visible = not cor.visible

        # toggle the visiblity of the objects interpolation holes
        for k, v in cont.iteritems():
            if k.startswith('{}-interpolation-line'.format(obj.name)):
                v.visible = not v.visible
            elif k == '{}-interpolation-indicator'.format(obj.name):
                v.visible = not v.visible

        ihs = obj.hole.interpolation_holes
        if ihs:
            for ih in set(ihs):
                ihid = ih.id
                na = '{}_cor'.format(ihid)
                nb = '{}-interpolation-indicator'.format(ihid)
                if na in cont:
                    c = cont[na]
                elif nb in cont:
                    c = cont[nb]

                c.visible = not c.visible

# ============= EOF =============================================
