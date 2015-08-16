# ===============================================================================
# Copyright 2013 Jake Ross
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
from chaco.data_label import draw_arrow
from chaco.label import Label
from chaco.plot_label import PlotLabel
from enable.colors import convert_from_pyqt_color
from enable.font_metrics_provider import font_metrics_provider
from kiva.trait_defs.kiva_font_trait import KivaFont
from traits.api import Array, Int, Float, Str, Color, Bool, List
from chaco.abstract_overlay import AbstractOverlay
from enable.tools.drag_tool import DragTool
# ============= standard library imports ========================
from numpy import where, array
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.graph.tools.info_inspector import InfoOverlay, InfoInspector
from pychron.pychron_constants import PLUSMINUS


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


class SpectrumTool(InfoInspector, BasePlateauOverlay):
    nsigma = Int(2)
    # metadata_changed = Event
    # current_position = None
    # current_screen = None
    analyses = List

    def hittest(self, screen_pt, threshold=20):
        comp = self.component

        ndx = self._get_section(screen_pt)
        ys = comp.value.get_data()[::2]
        if ndx < len(ys):
            yd = ys[ndx]

            e = comp.errors[ndx * 2] * self.nsigma
            yl, yu = comp.y_mapper.map_screen(array([yd - e, yd + e]))
            # print ys
            # print ndx, yd, yd+e, yd-e, yu, yl, screen_pt[1], self.nsigma
            if yu - yl < 1:
                yu += 1
                yl -= 1

            if yl < screen_pt[1] < yu:
                return ndx

    # def normal_mouse_move(self, event):
    # xy=event.x, event.y
    # pos=self.hittest(xy)
    # if pos is not None:
    # # if isinstance(pos, tuple):
    # self.current_position = pos
    # self.current_screen = xy
    #         # event.handled = True
    #     else:
    #         self.current_position = None
    #         self.current_screen = None
    #     self.metadata_changed = True

    def normal_left_down(self, event):
        if event.handled:
            return

        pt = event.x, event.y
        ndx = self.hittest(pt)
        if ndx is not None:
            sels = self.component.index.metadata['selections']
            self.component.index.metadata['selections'] = list(set(sels) ^ {ndx})
            self.component.request_redraw()
            event.handled = True

    def assemble_lines(self):
        idx = self.current_position
        comp = self.component

        e = comp.errors[idx * 2]
        ys = comp.value.get_data()[::2]
        v = ys[idx]

        low_c = 0 if idx == 0 else self.cumulative39s[idx - 1]

        an = self.analyses[idx]
        return ['RunID={}'.format(an.record_id),
                'Tag={}'.format(an.tag),
                'Status={}'.format(an.status_text),
                u'{}={} {}{} (1\u03c3)'.format(comp.container.y_axis.title, floatfmt(v), PLUSMINUS,
                                               floatfmt(e)),
                'Cumulative. Ar39={}-{}'.format(floatfmt(low_c),
                                                floatfmt(self.cumulative39s[idx]))]

    def normal_mouse_move(self, event):
        pt = event.x, event.y
        if self.hittest(pt) is not None and not event.handled:
            event.window.set_pointer('cross')
            hover = self._get_section(pt)
            self.component.index.metadata['hover'] = [hover]
            self.current_position = hover
            self.current_screen = pt
        else:
            event.window.set_pointer('arrow')
            self.component.index.metadata['hover'] = None

            self.current_position = None
            self.current_screen = None

        self.metadata_changed = True


class SpectrumInspectorOverlay(InfoOverlay):
    pass
    # @on_trait_change('tool:metadata_changed')
    # def _update_(self, new):
    # print 'asdf', new
    # tool =Any
    # @on_trait_change('tool:current_section')
    # def handle(self, new):
    # if new>=0:
    # self.visible=True
    # else:
    # self.visible=False
    #
    # def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
    # print 'pasdasfd'
    # with gc:


class SpectrumErrorOverlay(AbstractOverlay):
    nsigma = Int(1)
    alpha = Float
    use_fill = Bool(False)
    selections = List
    use_user_color = Bool(False)
    user_color = Color

    def overlay(self, component, gc, *args, **kw):
        comp = self.component
        with gc:
            gc.clip_to_rect(comp.x, comp.y, comp.width, comp.height)

            xs = comp.index.get_data()
            ys = comp.value.get_data()
            es = comp.errors
            # sels = comp.index.metadata['selections']
            sels = self.selections
            n = len(xs)
            xs = xs.reshape(n / 2, 2)
            ys = ys.reshape(n / 2, 2)
            es = es.reshape(n / 2, 2)

            if self.use_fill:
                alpha = self.alpha * 0.01
                func = gc.fill_path
            else:
                alpha = 1.0
                func = gc.stroke_path

            color = map(lambda x: x / 255., self.user_color.toTuple())

            color = color[0], color[1], color[2], alpha
            if abs(alpha - 0.3) < 0.1:
                selection_color = (0.75, 0, 0)
            else:
                selection_color = color[0], color[1], color[2], 0.3

            n = len(xs)
            for i, ((xa, xb), (ya, yb), (ea, eb)) in enumerate(zip(xs, ys, es)):
                ea *= self.nsigma
                # eb *= self.nsigma
                p1 = xa, ya - ea
                p2 = xa, ya + ea
                p3 = xb, ya - ea
                p4 = xb, ya + ea
                p1, p2, p3, p4 = comp.map_screen([p1, p2, p3, p4])
                x = p1[0]
                y = p1[1]
                w = p3[0] - p1[0]
                h = p2[1] - p1[1]

                c = selection_color if i in sels else color

                gc.set_fill_color(c)
                gc.set_stroke_color(c)

                gc.rect(x, y, w, h)
                func()
                if i > 0 and i <= n:
                    # draw verticals
                    px, y, e = pp
                    y1 = min((y - e), ya - ea)
                    y2 = max((y + e), ya + ea)
                    p1, p2 = comp.map_screen([(px, y1), (px, y2)])
                    with gc:
                        gc.begin_path()
                        gc.move_to(*p1)
                        gc.line_to(*p2)

                        gc.close_path()
                        gc.stroke_path()

                pp = (xb, ya, ea)


class PlateauTool(DragTool):
    def normal_mouse_move(self, event):
        if self.is_draggable(event.x, event.y):
            event.window.set_pointer('hand')
        else:
            event.window.set_pointer('arrow')

    # def normal_mouse_move(self, event):
    # if self.is_draggable(event.x, event.y):
    # event.handled = True
    #
    # def normal_left_down(self, event):
    # if self.is_draggable(event.x, event.y):
    # event.handled = True

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
        # event.handled = True
        plot.invalidate_and_redraw()


class PlateauOverlay(BasePlateauOverlay):
    plateau_bounds = Array
    # y = Float
    dragged = False
    id = Str

    plateau_label = PlotLabel
    info_txt = Str
    label_visible = True
    label_offset = 0
    label_font = KivaFont
    # label_font_size = 10
    extend_end_caps = True
    ages_errors = Array
    ages = Array
    nsigma = Int(2)
    line_color = Color('red')
    line_width = Float(1.0)
    selections = List
    arrow_visible = Bool

    def hittest(self, pt, threshold=7):
        x, y = pt
        pts = self._get_line()
        if pts is not None:
            pt1, pt2, y1, y2 = pts
            if pt1[0] <= x <= pt2[0]:
                if abs(y - pt1[1]) <= threshold:
                    return True

    def _get_line(self):
        """
            reurns screen values for start plat, end plat, error mag at start, error mag at end
        """
        cs = self.cumulative39s
        ps = self.plateau_bounds
        if ps[0] == ps[1]:
            return

        sidx = ps[0]
        eidx = ps[1]
        sels = self.selections
        # sels = self.component.index.metadata['selections']
        while sidx in sels:
            sidx += 1

        while eidx in sels:
            eidx -= 1

        eidx += 1

        cstart = cs[sidx]
        cend = cs[eidx]

        aes = self.ages
        es = self.age_errors
        eidx -= 1
        estart = es[sidx] * self.nsigma
        eend = es[eidx] * self.nsigma

        ystart = aes[sidx]
        yend = aes[eidx]

        y = self._get_plateau_y()

        a = ystart - estart if y < ystart else ystart + estart
        b = yend - eend if y < yend else yend + eend

        pt1, pt2, up1, up2 = self.component.map_screen([(cstart, y), (cend, y), (cstart, a), (cend, b)])
        # up1, up2 = self.component.map_screen([(cstart, a), (cend, b)])
        y1, y2 = up1[1], up2[1]

        return pt1, pt2, y1, y2

    def _get_plateau_y(self, screen_offset=100):
        """
            return y for plateau in data space

            if y value greater than bounds set y to ybounds - 50px
        :param screen_offset:
        :return:
        """
        comp = self.component

        y = self.y
        oy = comp.value_mapper.map_data(0)
        delta = comp.value_mapper.map_data(screen_offset) - oy
        y += delta

        by = comp.value_range.high
        if y > by:
            delta = comp.value_mapper.map_data(50) - oy
            y = by - delta
        return y

    def _draw_end_caps(self, gc, x1, x2, y):
        gc.lines([(x1, y - 10), (x1, y + 10)])
        gc.lines([(x2, y - 10), (x2, y + 10)])

    def _draw_extended_end_caps(self, gc, x1, x2, y, y1, y2):
        if y1 > y:
            gc.lines([(x1, y - 10), (x1, y1 - 5)])
        else:
            gc.lines([(x1, y + 10), (x1, y1 + 5)])

        if y2 > y:
            gc.lines([(x2, y - 10), (x2, y2 - 5)])
        else:
            gc.lines([(x2, y + 10), (x2, y2 + 5)])

            # if y1 < y and y2<y:
            # gc.lines([(x1, y1+5), (x1, y + 10)])
            # gc.lines([(x2, y2+5), (x2, y + 10)])
            # elif y1> y and y2>y:
            # gc.lines([(x1, y - 10),(x1, y1 + 5)])
            # gc.lines([(x2, y - 10),(x2, y2 + 5)])

    def overlay(self, component, gc, *args, **kw):
        points = self._get_line()
        if points:
            pt1, pt2, y1, y2 = points
            with gc:
                comp = self.component
                gc.clip_to_rect(comp.x, comp.y, comp.width, comp.height)
                color = convert_from_pyqt_color(None, None, self.line_color)
                gc.set_stroke_color(color)
                gc.set_line_width(self.line_width)

                y = pt1[1]
                x1 = pt1[0] + 1
                x2 = pt2[0] - 1
                gc.lines([(x1, y), (x2, y)])

                self._draw_end_caps(gc, x1, x2, y)
                gc.draw_path()
                if self.arrow_visible:
                    draw_arrow(gc, (x1 + 5, y), (x1, y), color)
                    draw_arrow(gc, (x2 - 5, y), (x2, y), color)

                # add end caps
                if self.extend_end_caps:
                    gc.set_line_width(1)
                    self._draw_extended_end_caps(gc, x1, x2, y, y1, y2)

                gc.draw_path()

                if self.label_visible:
                    label = self._get_plateau_label(x1, x2, y)
                    label.overlay(component, gc)

    def _get_plateau_label(self, x1, x2, y):

        if self.layout_needed or not self.plateau_label:
            p = self.plateau_label
        else:
            comp = self.component
            x = x1 + (x2 - x1) * 0.5

            dummy_gc = font_metrics_provider()
            l = Label(text=self.info_txt)
            w, h = l.get_bounding_box(dummy_gc)

            xa = x + w / 2.
            hjustify = 'center'
            if xa > comp.x2:
                d = xa - comp.x2
                x -= d
            elif x - w / 2. < comp.x:
                x = comp.x + 5
                hjustify = 'left'

            x = max(comp.x, x)
            p = PlotLabel(text=self.info_txt,
                          font=self.label_font,
                          # font='modern {}'.format(self.label_font_size),
                          color=self.line_color,
                          hjustify=hjustify,
                          border_visible=True,
                          bgcolor='white',
                          x=x,
                          y=y + 10)
            self.plateau_label = p

        return p

# ============= EOF =============================================
