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
from __future__ import absolute_import

# ============= enthought library imports =======================
import math

from traits.api import List

from pychron.canvas.canvas2D.scene.primitives.base import Connectable
from pychron.canvas.canvas2D.scene.primitives.primitives import Bordered, Circle, Label
from pychron.canvas.canvas2D.scene.primitives.rounded import (
    RoundedRectangle,
    rounded_rect,
)


# ============= standard library imports ========================
# ============= local library imports  ==========================


class Switch(Connectable, Circle):
    associations = List
    owned = False
    soft_lock = False
    is_stale = False
    is_interlocked = False
    is_forced = False
    owner_name = ""
    cannot_actuate_reason = ""
    connected_volume = 0
    description = ""
    network_region_id = ""
    network_dominant_source = ""
    network_dominant_source_node = ""
    network_blocked_boundaries = None
    network_side_volumes = None

    def apply_visual_state(self, state) -> None:
        self.state = state.is_open
        self.owned = state.is_owned
        self.soft_lock = state.is_locked
        self.is_stale = state.is_stale
        self.is_interlocked = state.is_interlocked
        self.is_forced = state.is_forced
        self.owner_name = state.owner
        self.cannot_actuate_reason = state.cannot_actuate_reason
        self.connected_volume = state.connected_volume
        self.description = state.description or self.description
        self.network_region_id = state.network_region_id
        self.network_dominant_source = state.network_dominant_source
        self.network_dominant_source_node = state.network_dominant_source_node
        self.network_blocked_boundaries = list(state.network_blocked_boundaries or [])
        self.network_side_volumes = list(state.network_side_volumes or [])

    def get_tooltip_text(self) -> str:
        pieces = ["Switch={}".format(self.name)]
        if self.description:
            pieces.append("Desc={}".format(self.description))
        if self.owner_name:
            pieces.append("Owner={}".format(self.owner_name))
        if self.soft_lock:
            pieces.append("Locked=Yes")
        if self.is_stale:
            pieces.append("Stale=Yes")
        if self.connected_volume:
            pieces.append("Volume={:0.2f}".format(self.connected_volume))
        if self.network_region_id:
            pieces.append("Region={}".format(self.network_region_id))
        if self.network_dominant_source:
            pieces.append("Source={}".format(self.network_dominant_source))
        if self.network_dominant_source_node:
            pieces.append("SourceNode={}".format(self.network_dominant_source_node))
        if self.network_blocked_boundaries:
            pieces.append(
                "Boundaries={}".format(",".join(self.network_blocked_boundaries))
            )
        if self.network_side_volumes:
            pieces.append(
                "SideVolumes={}".format(
                    ",".join("{:0.2f}".format(v) for v in self.network_side_volumes)
                )
            )
        if self.cannot_actuate_reason:
            pieces.append("Blocked={}".format(self.cannot_actuate_reason))
        return "\n".join(pieces)

    def set_label(self, label, offset_x, offset_y, **kw):
        lb = Label(
            0,
            0,
            text=label,
            hjustify="center",
            soffset_x=offset_x,
            soffset_y=offset_y,
            # font='modern 9',
            use_border=False,
            **kw
        )

        self.primitives.append(lb)
        return lb

    def _render(self, gc):
        x, y = self.get_xy()
        r = self.radius
        r = self.map_dimension(r)

        if self.state:
            gc.set_fill_color(self._convert_color(self.active_color))
        else:
            gc.set_fill_color(self._convert_color(self.default_color))

        gc.arc(x + r, y + r / 2.0, r, 0, 360)
        gc.set_stroke_color((0, 0, 0))
        gc.set_line_width(2)
        gc.draw_path()

        if self.soft_lock:
            gc.set_stroke_color((0.15, 0.35, 0.95, 1.0))
            gc.arc(x + r, y + r / 2.0, r + 2, 0, 360)
            gc.stroke_path()

        for p in self.primitives:
            p.x, p.y = self.x, self.y
            p.render(gc)

    # def is_in(self, sx, sy):
    #     x, y = self.get_xy()
    #     r = self.map_dimension(self.radius)
    #     return ((x + r - sx) ** 2 + (y + r / 2.0 - sy) ** 2) ** 0.5 < r


class BaseValve(Connectable):
    soft_lock = False
    owned = False
    oactive_color = (0, 1, 0)
    description = ""
    locked_color = (0.15, 0.35, 0.95, 1.0)
    owned_color = (0.95, 0.6, 0.1, 1.0)
    disconnected_color = (0.45, 0.45, 0.45, 1.0)
    owner_name = ""
    is_forced = False
    is_interlocked = False
    is_stale = False
    cannot_actuate_reason = ""
    last_state_timestamp = ""
    last_readback_timestamp = ""
    state_source = "unknown"
    connected_volume = 0
    simulation_mode = False
    network_region_id = ""
    network_dominant_source = ""
    network_dominant_source_node = ""
    network_blocked_boundaries = None
    network_side_volumes = None

    def toyaml(self):
        y = super(BaseValve, self).toyaml()
        del y["color"]
        del y["display_name"]
        del y["border_width"]
        del y["fill"]

        return y

    def get_tooltip_text(self) -> str:
        if self.state is None:
            state = "Unknown"
        else:
            state = "Open" if self.state else "Closed"
        if self.soft_lock:
            state = "{} (Locked)".format(state)

        owner = self.owner_name if self.owner_name else ("Yes" if self.owned else "No")
        lines = [
            "Valve={}".format(self.name),
            "Desc={}".format(self.description),
            "State={}".format(state),
            "Owned={}".format(owner),
        ]
        if self.is_interlocked:
            lines.append("Interlocked=Yes")
        if self.is_stale:
            lines.append("Stale=Yes")
        if self.connected_volume:
            lines.append("Volume={:0.2f}".format(self.connected_volume))
        if self.network_region_id:
            lines.append("Region={}".format(self.network_region_id))
        if self.network_dominant_source:
            lines.append("Source={}".format(self.network_dominant_source))
        if self.network_dominant_source_node:
            lines.append("SourceNode={}".format(self.network_dominant_source_node))
        if self.network_blocked_boundaries:
            lines.append("Boundaries={}".format(",".join(self.network_blocked_boundaries)))
        if self.network_side_volumes:
            lines.append(
                "SideVolumes={}".format(
                    ",".join("{:0.2f}".format(v) for v in self.network_side_volumes)
                )
            )
        if self.cannot_actuate_reason:
            lines.append("Blocked={}".format(self.cannot_actuate_reason))
        return "\n".join(lines)

    def apply_visual_state(self, state) -> None:
        self.state = state.is_open
        self.soft_lock = state.is_locked
        self.owned = state.is_owned
        self.owner_name = state.owner
        self.is_forced = state.is_forced
        self.is_interlocked = state.is_interlocked
        self.is_stale = state.is_stale
        self.cannot_actuate_reason = state.cannot_actuate_reason
        self.last_state_timestamp = state.last_state_timestamp
        self.last_readback_timestamp = state.last_readback_timestamp
        self.state_source = state.state_source
        self.connected_volume = state.connected_volume
        self.description = state.description or self.description
        self.network_region_id = state.network_region_id
        self.network_dominant_source = state.network_dominant_source
        self.network_dominant_source_node = state.network_dominant_source_node
        self.network_blocked_boundaries = list(state.network_blocked_boundaries or [])
        self.network_side_volumes = list(state.network_side_volumes or [])

    def _draw_visual_state_badges(self, gc, x, y, w, h):
        if self.soft_lock:
            self._draw_badge(gc, x + 2, y + h - 10, self.locked_color)
        if self.owned:
            self._draw_badge(gc, x + w - 10, y + h - 10, self.owned_color)
        if self.is_interlocked:
            self._draw_badge(gc, x + 2, y + 2, (0.85, 0.2, 0.2, 1.0))
        if self.is_stale:
            self._draw_badge(gc, x + w - 10, y + 2, self.disconnected_color)

    def _draw_badge(self, gc, x, y, color):
        with gc:
            gc.set_fill_color(color)
            gc.set_stroke_color((0, 0, 0))
            gc.rect(x, y, 8, 8)
            gc.draw_path()

    def _draw_soft_lock_rect(self, gc, line_width=5):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color(self.locked_color)
                gc.set_line_width(line_width)
                x, y = self.get_xy()
                width, height = self.get_wh()
                rounded_rect(gc, x, y, width, height, 3)

    def _draw_owned_rect(self, gc, line_width=3):
        if self.owned:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color(self.owned_color)
                gc.set_line_width(line_width)
                x, y = self.get_xy()
                width, height = self.get_wh()
                rounded_rect(gc, x, y, width, height, 3)


class ManualSwitch(BaseValve, RoundedRectangle):
    width = 1.6622795630156608
    height = 2
    corner_radius = 4
    use_border_gaps = False

    def _rotate(self, gc, angle):
        x, y = self.get_xy()
        w, h = self.get_wh()
        xx = x + w / 2
        yy = y + h / 2.0
        gc.translate_ctm(xx, yy)
        gc.rotate_ctm(math.radians(angle))
        gc.translate_ctm(-xx, -yy)

    def _render_textbox(self, gc, *args, **kw):
        with gc:
            gc.translate_ctm(0, 25)
            super(ManualSwitch, self)._render_textbox(gc, *args, **kw)

    def _render(self, gc):
        super(ManualSwitch, self)._render(gc)
        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()
        self._draw_soft_lock_rect(gc)
        self._draw_owned_rect(gc)
        self._draw_visual_state_badges(gc, x, y, w, h)


class Valve(BaseValve, RoundedRectangle):
    width = 2
    height = 2
    corner_radius = 4
    use_border_gaps = False
    not_connected_color = (100, 100, 100)
    tag = "valve"

    def __init__(self, *args, **kw):
        super(Valve, self).__init__(*args, **kw)
        self.state = None

    def _get_border_color(self):
        c = self.get_color()
        c = [ci / 2.0 for ci in c]
        if len(c) == 4:
            c[3] = 1

        return c

    def set_stroke_color(self, gc):
        gc.set_stroke_color(self.get_color())

    def set_fill_color(self, gc):
        gc.set_fill_color(self.get_color())

    def get_color(self):
        if self.state is None:
            c = self._convert_color(self.disconnected_color)
        else:
            if self.state:
                c = self._convert_color(self.active_color)
            else:
                c = self._convert_color(self.default_color)

        return c

    def _render(self, gc):
        x, y = self.get_xy(clear_layout_needed=False)
        w, h = self.get_wh()
        super(Valve, self)._render(gc)

        self._draw_soft_lock(gc)

        self._draw_owned(gc)
        self._draw_state_indicator(gc, x, y, w, h)
        self._draw_visual_state_badges(gc, x, y, w, h)

    def _draw_soft_lock(self, gc):
        self._draw_soft_lock_rect(gc, line_width=5)

    def _draw_owned(self, gc):
        self._draw_owned_rect(gc, line_width=3)

    def _draw_state_indicator(self, gc, x, y, w, h):
        if self.state is False:
            gc.set_stroke_color((0, 0, 0))
            l = 5
            o = 2
            gc.set_line_width(2)
            with gc:
                gc.translate_ctm(x, y)

                # lower left
                gc.move_to(o, o)
                gc.line_to(o + l, o + l)

                # upper left
                gc.move_to(o, h - o)
                gc.line_to(o + l, h - o - l)

                # lower right
                gc.move_to(w - o, o)
                gc.line_to(w - o - l, o + l)

                # upper left
                gc.move_to(w - o, h - o)
                gc.line_to(w - o - l, h - o - l)
                gc.draw_path()


def rounded_triangle(gc, cx, cy, width, height, cr):
    w2 = width / 2.0
    gc.translate_ctm(cx + cr / 3, cy)

    gc.begin_path()
    gc.move_to(w2, 0)
    gc.arc_to(width, 0, width - cr, cr, cr)
    gc.arc_to(w2, height + cr, w2 - cr, height, cr)
    gc.arc_to(0, 0, cr, 0, cr)
    gc.line_to(w2, 0)
    gc.draw_path()


class RoughValve(BaseValve, Bordered):
    width = 3
    height = 2
    border_width = 3

    def _render(self, gc):
        cx, cy = self.get_xy(clear_layout_needed=False)
        #         cx, cy = 200, 50
        width, height = self.get_wh()
        #         width += 10
        cr = 4
        func = lambda: rounded_triangle(gc, cx, cy, width, height, cr)
        if self.use_border:
            with gc:
                gc.set_line_width(self.border_width)
                c = self._get_border_color()
                gc.set_stroke_color(c)
                func()
        else:
            func()

        self._draw_state_indicator(gc, cx, cy, width, height, cr)
        self._render_name(gc, cx, cy, width, height)
        self._draw_owned(gc, func)
        self._draw_soft_lock(gc, func)
        self._draw_visual_state_badges(gc, cx, cy, width, height)

    def _draw_owned(self, gc, func):
        if self.owned:
            with gc:
                gc.set_fill_color((0, 0, 0, 0))
                gc.set_stroke_color(self.owned_color)
                gc.set_line_width(2)
                func()
                gc.draw_path()

    def _draw_soft_lock(self, gc, func):
        if self.soft_lock:
            with gc:
                gc.set_fill_color((0, 0, 1, 0))
                gc.set_stroke_color(self.locked_color)
                gc.set_line_width(4)
                func()
                gc.draw_path()

    def _draw_state_indicator(self, gc, x, y, w, h, cr):
        if self.state is False:
            with gc:
                gc.translate_ctm(x, y)
                gc.set_line_width(2)
                gc.set_stroke_color((0, 0, 0, 1))

                l = 6
                o = 2

                # lower left
                gc.move_to(o + cr, o)
                gc.line_to(o + cr + l, o + l - 3)

                # lower right
                gc.move_to(w - o - cr, o)
                gc.line_to(w - o - cr - l, o + l - 3)

                # upper center
                w2 = w / 2.0 + 1
                gc.move_to(w2, h)
                gc.line_to(w2, h - l)

                gc.draw_path()


# class RoughValve2(BaseValve):
#     def _render_(self, gc):
#         cx, cy = self.get_xy()
#         width, height = self.get_wh()
#
#         w2 = width / 2
#         x1 = cx
#         x2 = cx + width
#         x3 = cx + w2
#
#         y1 = cy
#         y2 = y1
#         y3 = cy + height
#
#         gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])
#         gc.fill_path()
#
#         #         gc.set_stroke_color((0, 0, 0))
#         #         gc.lines([(x1, y1), (x2, y2), (x3, y3), (x1, y1)])
#
#
#         #         func = gc.lines
#         #         args = (([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x2, y2)]),)
#         #        args = (x - 2, y - 2, width + 4, height + 4)
#
#         #         self._draw_soft_lock(gc, func, args)
#         #         self._draw_owned(gc, func, args)
#         self._draw_state_indicator(gc, cx, cy, width, height)
#         self._render_name(gc, cx, cy, width, height)
#
#     def _draw_owned(self, gc, func, args):
#         if self.soft_lock:
#             with gc:
#                 gc.set_fill_color((0, 0, 0, 0))
#                 gc.set_stroke_color((0, 0, 1))
#                 gc.set_line_width(5)
#                 func(*args)
#                 gc.draw_path()
#
#     def _draw_soft_lock(self, gc, func, args):
#         if self.soft_lock:
#             with gc:
#                 gc.set_fill_color((0, 0, 1, 0))
#                 gc.set_stroke_color((0, 0, 1))
#                 gc.set_line_width(5)
#                 func(*args)
#                 gc.draw_path()
#
#     def _draw_state_indicator(self, gc, x, y, w, h):
#         if not self.state:
#             l = 7
#             w2 = w / 2.
#             w3 = w / 3.
#
#             gc.set_line_width(2)
#             gc.move_to(x + w2, y + h)
#             gc.line_to(x + w2, y + h - l)
#             gc.draw_path()
#
#             gc.move_to(x, y)
#             gc.line_to(x + w3, y + l)
#             gc.draw_path()
#
#             gc.move_to(x + w, y)
#             gc.line_to(x + w - w3, y + l)
#             gc.draw_path()

# ============= EOF =============================================
