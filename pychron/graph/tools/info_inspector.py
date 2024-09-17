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
from __future__ import absolute_import

from chaco.abstract_overlay import AbstractOverlay
from chaco.tools.scatter_inspector import ScatterInspector, ScatterInspectorEvent
from enable.base_tool import BaseTool, KeySpec
from kiva.fonttools import Font

# from pychron.pipeline.plot.inspector_item import BaseInspectorItem
from six.moves import range
from six.moves import zip
from traits.api import Event, Instance


def intersperse(m, delim):
    """
    intersperse ```delim``` in m
     m=[1,2,3]
     delim='---'
     result=[1,'---',2,'---',3]

    """
    m = iter(m)
    yield next(m)
    for x in m:
        yield delim
        yield x


class InfoInspector(ScatterInspector):
    # class InfoInspector(BaseTool):
    metadata_changed = Event
    current_position = None
    current_screen = None
    # use_pane = False
    # inspector_item = Event
    # inspector_item_klass = BaseInspectorItem
    event_queue = None
    hittest_threshold = 5

    def __init__(self, *args, **kw):
        super(InfoInspector, self).__init__(*args, **kw)
        self.selection_mode = "multi"
        self.multiselect_modifier = KeySpec(None)

    # select_event = Event

    # def normal_left_down(self, event):
    #     pass
    # print('infaso', event, id(event))
    # if not event.handled:
    #     super(InfoInspector, self).normal_left_down(event)

    def normal_left_down(self, event):
        if not event.handled:
            super(InfoInspector, self).normal_left_down(event)

    def normal_left_dclick(self, event):
        for sel in self.component.index.metadata[self.selection_metadata_name]:
            self.inspector_event = ScatterInspectorEvent(
                event_type="deselect", event_index=sel
            )
        self.component.index.metadata[self.selection_metadata_name] = []

    def normal_mouse_move(self, event):
        xy = event.x, event.y
        try:
            pos = self.component.hittest(xy, threshold=self.hittest_threshold)
            event.window.set_pointer("cross")
        except (IndexError, ValueError):
            event.window.set_pointer("arrow")
            return

        if isinstance(pos, (tuple, list)):
            try:
                self.current_position = (pos[0][0], pos[1][0])
            except IndexError:
                self.current_position = pos
            self.current_screen = xy
            event.handled = True
        else:
            event.window.set_pointer("arrow")
            self.current_position = None
            self.current_screen = None

        if self.event_queue is not None:
            self.event_queue[id(self)] = self.current_position is not None

        # if self.use_pane:
        #     self._generate_inspector_event()

        self.metadata_changed = True

    def assemble_lines(self):
        return

    def normal_mouse_leave(self, event):
        self.current_screen = None
        self.current_position = None
        self.metadata_changed = True
        # event.window.set_pointer('arrow')

    # def _generate_inspector_event(self):
    #     if self.current_position:
    #         txt = '\n'.join(self.assemble_lines())
    #     else:
    #         txt = ''
    #         if self.event_queue:
    #             if not any((v for v in self.event_queue.values())):
    #                 txt = ''
    #             else:
    #                 txt = None
    #
    #     if txt or txt == '':
    #         i = self.inspector_item_klass()
    #         i.text = txt
    #         self.inspector_item = i


class InfoOverlay(AbstractOverlay):
    """
    abstract class for displaying hover data
    """

    tool = Instance(BaseTool)
    visible = False

    def _update(self):
        if self.tool.current_position is not None:
            self.visible = True
        else:
            self.visible = False
        self.request_redraw()

    def overlay(self, plot, gc, *args, **kw):
        # with gc:
        #     self._draw_indicator(gc)

        with gc:
            lines = self.tool.assemble_lines()
            if lines:
                lines = [li for li in lines if li and li.strip()]
                self._draw_info(plot, gc, lines)

                # self.visible = False

    def _draw_indicator(self, gc):
        cx, cy = self.tool.current_screen
        gc.set_fill_color((1, 1, 1, 0.5))
        gc.arc(cx, cy, self.tool.hittest_threshold, 0, 360)
        gc.draw_path()

    def _draw_info(self, plot, gc, lines):
        if not self.tool.current_screen:
            return

        x, y = sx, sy = self.tool.current_screen

        size = 14
        gc.set_font(Font("Arial", size=size))
        gc.set_fill_color((0.8, 0.8, 0.8))

        lws, lhs = list(zip(*[gc.get_full_text_extent(mi)[:2] for mi in lines]))

        rect_width = max(lws) + 12
        rect_height = (max(lhs) + 4) * len(lhs) + 2

        xoffset = 15
        yoffset = -15
        gc.translate_ctm(xoffset, yoffset)

        # if the box doesnt fit in window
        # move left
        x2 = self.component.x2
        y2 = self.component.y2

        if x + xoffset + rect_width > x2:
            x = x2 - rect_width - xoffset - 1

        multi_column = 0
        h = max(lhs) + 4
        cheight = self.component.height
        if rect_height > cheight + 5 * h:
            multi_column = 2
        else:
            # move up if too tall

            if y + yoffset - rect_height < self.component.y:
                y = self.component.y + rect_height - yoffset

        # if current point within bounds of box, move box to left
        if x < sx:
            x = sx - rect_width - xoffset - 6

        if multi_column:
            gc.translate_ctm(x, self.component.y)
            gc.rect(0, -2, multi_column * rect_width, cheight - yoffset)
        else:
            gc.translate_ctm(x, y - rect_height)
            gc.rect(0, -2, rect_width, rect_height + 4)

        gc.draw_path()
        gc.set_fill_color((0, 0, 0))

        if multi_column:
            gen = (li for li in lines)
            for col in range(multi_column):
                i = 0
                for mi in gen:
                    if i == 0 and mi == "--------":
                        continue

                    yi = h * i
                    if yi > cheight:
                        break
                    gc.set_text_position(col * rect_width, y2 - yi)
                    gc.show_text(mi)
                    i += 1
        else:
            for i, mi in enumerate(lines[::-1]):
                gc.set_text_position(5, h * i + 5)
                gc.show_text(mi)

    def _tool_changed(self, old, new):
        if old:
            old.on_trait_change(self._update, "metadata_changed", remove=True)

        if new:
            new.on_trait_change(self._update, "metadata_changed")


# ============= EOF =============================================
