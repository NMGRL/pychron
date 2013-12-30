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
from chaco.plot_label import PlotLabel
from traits.api import Array, Int, Float,Str
from chaco.abstract_overlay import AbstractOverlay
#============= standard library imports ========================
from numpy import where, array
from enable.base_tool import BaseTool
from enable.tools.drag_tool import DragTool
#============= local library imports  ==========================

class BasePlateauOverlay(AbstractOverlay):
    cumulative39s = Array
    def _get_section(self, pt):
        d = self.component.map_data(pt)
        cs = self.cumulative39s
        t = where(cs < d)[0]
        if len(t):
            tt = t[-1] + 1
        else:
            tt = 0
        return tt

class SpectrumTool(BaseTool, BasePlateauOverlay):
    nsigma = Int(2)
    def hittest(self, screen_pt, threshold=20):
        comp = self.component

        ndx = self._get_section(screen_pt)
        ys = comp.value.get_data()[::2]
        if ndx < len(ys):
            yd = ys[ndx]
            e = comp.errors[ndx] * self.nsigma
            yl, yu = comp.y_mapper.map_screen(array([yd - e, yd + e]))

            if yl < screen_pt[1] < yu:
                return ndx

    def normal_left_down(self, event):
        if event.handled:
            return

        pt = event.x, event.y
        ndx = self.hittest(pt)
        if ndx is not None:
            sels = self.component.index.metadata['selections']
            self.component.index.metadata['selections'] = list(set(sels) ^ set([ndx]))
            self.component.request_redraw()

        event.handled = True

    def normal_mouse_move(self, event):
        pt = event.x, event.y
        if self.hittest(pt) is not None and not event.handled:
            event.window.set_pointer('cross')
            hover = self._get_section(pt)
            self.component.index.metadata['hover'] = [hover]

        else:
            event.window.set_pointer('arrow')
            self.component.index.metadata['hover'] = None

class SpectrumErrorOverlay(AbstractOverlay):
    nsigma = Int(1)
    def overlay(self, component, gc, *args, **kw):
        comp = self.component
        with gc:
            gc.clip_to_rect(comp.x, comp.y, comp.width, comp.height)

            xs = comp.index.get_data()
            ys = comp.value.get_data()
            es = comp.errors
            sels = comp.index.metadata['selections']

            n = len(xs)
            xs = xs.reshape(n / 2, 2)
            ys = ys.reshape(n / 2, 2)
            es = es.reshape(n / 2, 2)
            for i, ((xa, xb), (ya, yb), (ea, eb)) in enumerate(zip(xs, ys, es)):
                ea *= self.nsigma
                eb *= self.nsigma
                p1 = xa, ya - ea
                p2 = xa, ya + ea
                p3 = xb, ya - ea
                p4 = xb, ya + ea
                p1, p2, p3, p4 = comp.map_screen([p1, p2, p3, p4])
                x = p1[0]
                y = p1[1]
                w = p3[0] - p1[0]
                h = p2[1] - p1[1]
                if i in sels:
                    gc.set_fill_color((0.75, 0, 0))
                else:
                    c = comp.color
                    # if isinstance(c, str):
                    #     c = color_table[c]
                    c=(0,0,0,0.25)
                    gc.set_fill_color(c)
                gc.rect(x, y, w + 1, h)
                gc.fill_path()


class PlateauTool(DragTool):
    def normal_mouse_move(self, event):
        if self.is_draggable(event.x, event.y):
            event.handled = True

    def normal_left_down(self, event):
        if self.is_draggable(event.x, event.y):
            event.handled = True

    def is_draggable(self, x, y):
        return self.component.hittest((x, y))

    def drag_start(self, event):
        data_pt = self.component.component.map_data((event.x, event.y), all_values=True)
        self._prev_pt = data_pt
        event.handled = True

    def dragging(self, event):
        plot = self.component.component
        cur_pt = plot.map_data((event.x, event.y), all_values=True)
        dy = cur_pt[1] - self._prev_pt[1]
        self.component.y += dy
        self.component.dragged = True
        self._prev_pt = cur_pt
        event.handled = True
        plot.request_redraw()


class PlateauOverlay(BasePlateauOverlay):
    plateau_bounds = Array
    y = Float
    dragged = False

    plateau_label=PlotLabel
    info_txt=Str
    label_visible=True

    def hittest(self, pt, threshold=7):
        x, y = pt
        pts = self._get_line()
        if pts is not None:
            pt1, pt2 = pts
            if pt1[0] <= x <= pt2[0]:
                if abs(y - pt1[1]) <= threshold:
                    return True

    def _get_line(self):
        cs = self.cumulative39s
        ps = self.plateau_bounds
        if ps[0] == ps[1]:
            return
        cstart = cs[ps[0]]
        cend = cs[ps[1] + 1]
        y = self.y
        pt1, pt2 = self.component.map_screen([(cstart, y), (cend, y)])
        return pt1, pt2

    def overlay(self, component, gc, *args, **kw):

        line_width = 4
        points = self._get_line()
        if points:
            pt1, pt2 = points
            with gc:
                comp = self.component
                gc.clip_to_rect(comp.x, comp.y, comp.width, comp.height)
                gc.set_stroke_color((1, 0, 0))
                gc.set_line_width(line_width)

                y = pt1[1]
                x1 = pt1[0] + 1
                x2 = pt2[0] - 1
                gc.lines([(x1, y), (x2, y)])

                # add end caps
                gc.lines([(x1, y - 10), (x1, y + 10)])
                gc.lines([(x2, y - 10), (x2, y + 10)])
                gc.draw_path()

                #draw label
                # w, h, _, _ = gc.get_full_text_extent(self.plateau_label)
                # tx=x1+(w-(x2-x1)/2.0)
                # ty=y+5
                # gc.set_text_position(tx,ty)
                if self.label_visible:
                    label = self._get_plateau_label(x1, x2, y)
                    label.overlay(component, gc)

    def _get_plateau_label(self, x1, x2, y):
        if self.layout_needed or not self.plateau_label:
            p=self.plateau_label
        else:
            p=PlotLabel(text=self.info_txt,
                        x=x1+(x2-x1)*0.5,
                        y=y+10)
            self.plateau_label=p

        return p
#============= EOF =============================================
