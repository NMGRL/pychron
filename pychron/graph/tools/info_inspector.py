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
from enable.base_tool import BaseTool
from kiva.fonttools import Font
from traits.api import Event, Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.inspector_item import BaseInspectorItem


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


class InfoInspector(BaseTool):
    metadata_changed = Event
    current_position = None
    current_screen = None
    use_pane = False
    inspector_item = Event
    inspector_item_klass = BaseInspectorItem
    event_queue = None

    def normal_mouse_move(self, event):
        xy = event.x, event.y
        try:
            pos = self.component.hittest(xy)
            # event.window.set_pointer('cross')
        except IndexError:
            # event.window.set_pointer('arrow')
            return

        if isinstance(pos, (tuple, list)):
            self.current_position = pos
            self.current_screen = xy
            event.handled = True
        else:
            # event.window.set_pointer('arrow')
            self.current_position = None
            self.current_screen = None

        self.event_queue[id(self)] = self.current_position is not None

        if self.use_pane:
            self._generate_inspector_event()

        self.metadata_changed = True

    def assemble_lines(self):
        return

    def normal_mouse_leave(self, event):
        self.current_screen = None
        self.current_position = None
        self.metadata_changed = True
        # event.window.set_pointer('arrow')

    def _generate_inspector_event(self):
        if self.current_position:
            txt = '\n'.join(self.assemble_lines())
        else:
            txt = ''
            if self.event_queue:
                if not any((v for v in self.event_queue.itervalues())):
                    txt = ''
                else:
                    txt = None

        if txt or txt == '':
            i = self.inspector_item_klass()
            i.text = txt
            self.inspector_item = i


class InfoOverlay(AbstractOverlay):
    """
        abstract class for displaying hover data
    """
    tool = Instance(BaseTool)
    visible = False

    def _update_(self):
        if self.tool.current_position is not None:
            self.visible = True
        else:
            self.visible = False
        self.request_redraw()

    def overlay(self, plot, gc, *args, **kw):
        with gc:
            lines = self.tool.assemble_lines()
            if lines:
                lines = [li for li in lines if li and li.strip()]
                self._draw_info(plot, gc, lines)

                # self.visible = False

    def _draw_info(self, plot, gc, lines):
        if not self.tool.current_screen:
            return

        x, y = sx, sy = self.tool.current_screen

        gc.set_font(Font('Arial'))
        gc.set_fill_color((0.8, 0.8, 0.8))

        lws, lhs = zip(*[gc.get_full_text_extent(mi)[:2] for mi in lines])

        rect_width = max(lws) + 4
        rect_height = (max(lhs) + 2) * len(lhs)

        xoffset = 15
        yoffset = -15
        gc.translate_ctm(xoffset, yoffset)

        # if the box doesnt fit in window
        # move left
        x2 = self.component.x2
        y2 = self.component.y2

        if x + xoffset + rect_width > x2:
            x = x2 - rect_width - xoffset - 1

        # move down if to tall
        # if y + yoffset + rect_height > y2:
        #     y = y2 - rect_height - yoffset -1

        # if current point within bounds of box, move box to left
        if x < sx:
            x = sx - rect_width - xoffset - 6

        gc.translate_ctm(x, y - rect_height)
        gc.rect(0, -2, rect_width, rect_height + 4)
        gc.draw_path()
        gc.set_fill_color((0, 0, 0))

        h = max(lhs) + 2

        # this is cause the pointer to change to an IBeam if the cursor is close the the box
        # increase offsets? as a hack
        for i, mi in enumerate(lines[::-1]):
            gc.set_text_position(0, h * i)
            gc.show_text(mi)

    def _tool_changed(self, old, new):
        if old:
            old.on_trait_change(self._update_, 'metadata_changed', remove=True)

        if new:
            new.on_trait_change(self._update_, 'metadata_changed')

# ============= EOF =============================================
