# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import Any, Str
from chaco.api import AbstractOverlay, BaseTool
# =============standard library imports ========================
from numpy import vstack
# =============local library imports  ==========================

class RectSelectionOverlay(AbstractOverlay):
    tool = Any

    def overlay(self, component, gc, *args, **kw):
        with gc:
            sp = self.tool._start_pos
            ep = self.tool._end_pos
            if sp and ep:
                x, y = sp
                x2, y2 = ep
                gc.set_fill_color([1, 0, 0, 0.25])
                gc.set_stroke_color([1, 0, 0, 0.25])
                gc.rect(x, y, x2 - x + 1, y2 - y + 1)
                gc.draw_path()


class RectSelectionTool(BaseTool):
    """
    """

    filter_near_edge = False

    threshold = 5
    hover_metadata_name = Str('hover')
    persistent_hover = False
    selection_metadata_name = Str('selections')
    #    active = True
    _start_pos = None
    _end_pos = None
    group_id = 0

    def select_key_pressed(self, event):
        if event.character=='Esc':
            self._end_select(event)

    def normal_mouse_move(self, event):
        if event.handled:
            return

        plot = self.component
        index = plot.map_index((event.x, event.y), threshold=self.threshold)

        if index is not None:
            #            plot.index.metadata['mouse_xy'] = mxy

            plot.index.metadata[self.hover_metadata_name] = [index]
            if hasattr(plot, "value"):
                plot.value.metadata[self.hover_metadata_name] = [index]

        elif not self.persistent_hover:
            plot.index.metadata.pop(self.hover_metadata_name, None)
            if hasattr(plot, "value"):
                plot.value.metadata.pop(self.hover_metadata_name, None)

        return

    def _get_selection_token(self, event):
        return self.component.map_index((event.x, event.y), threshold=self.threshold)

    def _already_selected(self, token):
        already = False
        plot = self.component
        for name in ('index', 'value'):
            if not hasattr(plot, name):
                continue
            md = getattr(plot, name).metadata
            if md is None or self.selection_metadata_name not in md:
                continue

            # print token, md[self.selection_metadata_name]
            if token in md[self.selection_metadata_name]:
                already = True
                break

        return already

    def normal_left_dclick(self, event):
        if self._end_pos is None:
            #            print id(self), self.component, 'meta []'
            self.component.index.metadata[self.selection_metadata_name] = []
        elif abs(self._end_pos[0] - self._start_pos[0]) < 2 and \
                        abs(self._end_pos[1] - self._start_pos[1]) < 2:
            self.component.index.metadata[self.selection_metadata_name] = []

    def normal_left_down(self, event):

        if not event.handled:
            token = self._get_selection_token(event)
            if token is None:
                if not self._near_edge(event):
                    self._start_select(event)
            else:
                if self._already_selected(token):
                    self._deselect_token(token)
                else:
                    self._select_token(token)
                event.handled = True

    def select_mouse_leave(self, event):
        self._end_select(event)

    def _near_edge(self, event, tol=5):
        if self.filter_near_edge:
            ex = event.x
            ey = event.y
            x, x2 = self.component.x, self.component.x2
            y, y2 = self.component.y, self.component.y2

            if abs(ex - x) < tol or abs(ex - x2) < tol:
                return True

            elif abs(ey - y) < tol or abs(ey - y2) < tol:
                return True

    def _deselect_token(self, token):
        plot = self.component
        for name in ('index', 'value'):
            if not hasattr(plot, name):
                continue
            md = getattr(plot, name).metadata
            if self.selection_metadata_name in md:
                if token in md[self.selection_metadata_name]:
                    new = md[self.selection_metadata_name][:]
                    new.remove(token)

                    md[self.selection_metadata_name] = new

    def _select_token(self, token, append=True):
        plot = self.component
        for name in ('index',):
            if not hasattr(plot, name):
                continue
            md = getattr(plot, name).metadata
            selection = md.get(self.selection_metadata_name, None)
            if selection is None:
                md[self.selection_metadata_name] = [token]
            else:
                if append:
                    if token not in md[self.selection_metadata_name]:
                        new_list = md[self.selection_metadata_name] + [token]
                        md[self.selection_metadata_name] = new_list

    def select_left_up(self, event):
        self._update_selection()
        self._end_select(event)

    def select_mouse_move(self, event):
        self._end_pos = (event.x, event.y)
        self.component.request_redraw()

    def _update_selection(self):
        comp = self.component
        index = comp.index
        ind = []
        #        print self._start_pos, self._end_pos
        if self._start_pos and self._end_pos:
            x, y = self._start_pos
            x2, y2 = self._end_pos

            dx, dy = comp.map_data([x, y])
            dx2, dy2 = comp.map_data([x2, y2])

            datax = index.get_data()
            datay = comp.value.get_data()

            data = vstack([datax, datay]).transpose()

            ind = [i for i, (xi, yi) in enumerate(data) \
                   if (dx <= xi <= dx2 and dy >= yi >= dy2) or
                      (dx >= xi >= dx2) and dy <= yi <= dy2]

        selection = index.metadata[self.selection_metadata_name]
        nind = list(set(ind) ^ set(selection))
        index.metadata[self.selection_metadata_name] = nind
        # index.metadata_changed = True

    def _end_select(self, event):
        self.event_state = 'normal'
        event.window.set_pointer('arrow')

        self._end_pos = None
        self.component.request_redraw()

    def _start_select(self, event):
        self._start_pos = (event.x, event.y)
        #        self._end_pos = (event.x, event.y)
        self.event_state = 'select'
        event.window.set_pointer('cross')

# ============= EOF =====================================
