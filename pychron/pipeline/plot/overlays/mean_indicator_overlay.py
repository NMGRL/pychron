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
from chaco.abstract_overlay import AbstractOverlay
from chaco.plot_label import PlotLabel
from chaco.scatterplot import render_markers
from enable.markers import MarkerNameDict
from traits.api import Color, Instance, Str, Float, Int, Any, Enum, Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.pipeline.plot import LabelMoveTool
from pychron.pipeline.plot.point_move_tool import LabelMoveTool


class MovableMixin:
    current_screen_point = None
    altered_screen_point = None
    delta_screen_point = None
    ox = None
    oy = None
    offset_x = 0
    offset_y = 0

    def update_offset(self, dx, dy):
        if self.ox is None:
            self.ox, self.oy = self.x, self.y

        self.offset_x += dx
        self.offset_y += dy

    def get_current_point(self):
        data_pt = self.altered_screen_point
        if data_pt is None:
            data_pt = self.current_screen_point

        if data_pt is None:
            data_pt = (self.x, self.y)

        return data_pt


try:

    class XYPlotLabel(PlotLabel, MovableMixin):
        sx = Float
        sy = Float
        marker = None
        marker_size = None
        display_marker = False

        def _draw_overlay(self, gc, view_bounds=None, mode="normal"):
            """Draws the overlay layer of a component.

            Overrides PlotComponent.
            """
            # Perform justification and compute the correct offsets for
            # the label position
            width, height = self._label.get_bounding_box(gc)
            if self.hjustify == "left":
                x_offset = 0
            elif self.hjustify == "right":
                x_offset = self.width - width
            elif self.hjustify == "center":
                x_offset = int((self.width - width) / 2)

            if self.vjustify == "bottom":
                y_offset = 0
            elif self.vjustify == "top":
                y_offset = self.height - height
            elif self.vjustify == "center":
                y_offset = int((self.height - height) / 2)

            with gc:
                # XXX: Uncomment this after we fix kiva GL backend's clip stack
                # gc.clip_to_rect(self.x, self.y, self.width, self.height)

                # We have to translate to our position because the label
                # tries to draw at (0,0).
                gc.translate_ctm(self.x + x_offset, self.y + y_offset)
                if self.marker and self.display_marker:
                    self._draw_marker(gc, height)
                self._label.draw(gc)

            return

        def _draw_marker(self, gc, height):
            marker = self.marker
            marker_size = self.marker_size
            points = [(-10 - self.marker_size / 2, (height + marker_size) / 2)]
            # points = [(0, 100)]
            color = self.color
            line_width = 1
            outline_color = self.color
            render_markers(
                gc, points, marker, marker_size, color, line_width, outline_color
            )

        def do_layout(self):
            """Tells this component to do layout.

            Overrides PlotComponent.
            """
            if self.component is None:
                self._layout_as_component()
            return

        def hittest(self, pt):
            x, y = pt
            w, h = self.get_preferred_size()
            return abs(x - self.x) < w and abs(y - self.y) < h

        def _sx_changed(self):
            lw = self.get_preferred_size()[0] / 2.0
            x = self.sx + lw + 5
            x2 = self.component.x2
            if x + lw > x2:
                x = x2 - lw - 3

            self.x = x
            # self.altered_screen_point=(self.x, self.y)
            # print self.altered_screen_point
            self.current_screen_point = (self.x, self.y)

        def _sy_changed(self):
            self.y = self.sy + 10
            self.current_screen_point = (self.x, self.y)

        def set_altered(self):
            self.altered_screen_point = (self.x, self.y)

except TypeError:
    # documentation auto doc hack
    class XYPlotLabel:
        pass


def render_vertical_marker(gc, points, color, line_width, outline_color):
    with gc:
        gc.set_line_width(line_width)
        gc.set_stroke_color(outline_color)
        gc.set_fill_color(color)
        x, y = points[0]
        d = 5
        gc.begin_path()
        gc.move_to(x, y - d)
        gc.line_to(x, y + d)
        gc.draw_path()


def render_error_bar(gc, x1, x2, y, color, line_width=1, end_caps=True):
    with gc:
        gc.set_line_width(line_width)
        gc.set_stroke_color(color)
        gc.begin_path()
        gc.set_stroke_color(color)
        gc.move_to(x1, y)
        gc.line_to(x2, y)
        gc.draw_path()
        if end_caps:
            if not isinstance(end_caps, (float, int)):
                end_caps = 3

            render_end_cap(gc, x1, y, length=end_caps)
            render_end_cap(gc, x2, y, length=end_caps)


def render_end_cap(gc, x, y, length=3):
    with gc:
        l = length
        # gc.translate_ctm(x, y)
        gc.begin_path()
        gc.move_to(x, y - l)
        gc.line_to(x, y + l)
        # print x, y, y - l, y + l
        gc.draw_path()


try:

    class MeanIndicatorOverlay(AbstractOverlay, MovableMixin):
        color = Color
        label = Instance(PlotLabel)
        text = Str
        location = Enum("Mean", "Upper Right")
        # font = KivaFont('modern 15')
        x = Float
        error = Float
        nsigma = Int

        marker = Str("vertical")
        end_cap_length = Int(4)
        label_tool = Any
        group_id = Int
        group_marker = Str("circle")
        group_marker_size = Float(1)
        display_group_marker = Bool(True)

        def clear(self):
            self.altered_screen_point = None

        def hittest(self, pt, tol=5):
            x, y = pt
            if self.get_current_point():
                gx, gy = self.get_current_point()
                # print abs(gx-x)<tol , abs(gy-y)<tol
                return abs(gx - x) < tol and abs(gy - y) < tol
                # print x,y, gx, gy

        def _text_changed(self):
            label = self.label

            if label is None:
                label = XYPlotLabel(
                    component=self.component,
                    font=self.font,
                    text=self.text,
                    color=self.color,
                    marker=self.group_marker,
                    marker_size=self.group_marker_size,
                    display_marker=self.display_group_marker,
                    id="{}_label".format(self.id),
                )

                self.label = label
                self.overlays.append(label)
                tool = LabelMoveTool(component=label)
                self.tools.append(tool)
                self.label_tool = tool
            else:
                label.text = self.text
                # print self.label

        def _color_changed(self):
            color = self.color
            # if isinstance(color, str):
            #    color=color_table[color]
            self._color = [
                x / 255.0
                for x in (color.red(), color.green(), color.blue(), color.alpha())
            ]
            # self._color=color

        def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
            with gc:
                oc = other_component
                gc.clip_to_rect(oc.x, oc.y, oc.x2, oc.y2)
                points = self._gather_data()
                marker = self.marker

                color = self._color
                line_width = 1
                outline_color = self._color
                if marker != "vertical":
                    marker_size = 3
                    render_markers(
                        gc,
                        points,
                        marker,
                        marker_size,
                        color,
                        line_width,
                        outline_color,
                    )
                else:
                    render_vertical_marker(gc, points, color, line_width, outline_color)

                x, y = self.get_current_point()

                e = self.error * max(1, self.nsigma)
                p1, p2 = self.component.map_screen([(self.x - e, 0), (self.x + e, 0)])

                render_error_bar(
                    gc, p1[0], p2[0], y, self._color, end_caps=self.end_cap_length
                )

            for o in self.overlays:
                o.overlay(other_component, gc, view_bounds=view_bounds, mode=mode)

        def _gather_data(self):
            comp = self.component
            x = comp.map_screen([(self.x, 0)])[0, 0]

            if self.altered_screen_point is None:
                if self.label:
                    if not self.label.altered_screen_point:
                        y = self.y
                        if self.location == "Upper Right":
                            x = comp.x2 - self.label.width
                            y = comp.y2 - 20 * self.group_id
                        elif self.location == "Upper Left":
                            x = comp.x + 10
                            y = comp.y2 - 20 * self.group_id
                        elif self.location == "Lower Right":
                            x = comp.x2 - self.label.width
                            y = 20 * self.group_id
                        elif self.location == "Lower Left":
                            x = comp.x + 10
                            y = 20 * self.group_id

                        self.label.sx = x
                        self.label.sy = y
                self.current_screen_point = (x, self.y)

                return [(x, self.y)]
            else:
                if self.label:
                    if not self.label.altered_screen_point:
                        self.label.sx, self.label.sy = self.altered_screen_point
                return [(x, self.altered_screen_point[1])]

        def set_x(self, x):
            self.x = x
            comp = self.component
            x = comp.map_screen([(self.x, 0)])[0, 0]
            if self.label:
                if not self.label.altered_screen_point:
                    self.label.sx = x
                    self.label.sy = self.y

            if self.altered_screen_point:
                self.altered_screen_point = (x, self.altered_screen_point[1])
            else:
                self.current_screen_point = (x, self.y)

except TypeError:
    # documentation auto doc hack
    class MeanIndicatorOverlay:
        pass


# ============= EOF =============================================
