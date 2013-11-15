#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from chaco.abstract_overlay import AbstractOverlay

#============= standard library imports ========================

#============= local library imports  ==========================


class RectSelectionTool(AbstractOverlay):
    '''
    '''

    _start_pos = None
    _end_pos = None
    _enabled = False

    def reset(self):
        '''
        '''
        self.event_state = 'normal'
        self._start_pos = None
        self._end_pos = None
        self._enabled = False

    def _start_select(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        self._start_pos = (event.x, event.y)
        self._end_pos = None
        self.event_state = 'selecting'

        self.selecting_mouse_move(event)

    def _end_select(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        self._end_pos = (event.x, event.y)
        self._end_selecting(event)

    def _end_selecting(self, event):
        '''
            @type event: C{str}
            @param event:
        '''

        # get all items in the selection area
        self._get_selected_items()

        self.reset()

        self.component.request_redraw()
    def _get_selected_items(self):
        '''
        '''

        self.component.selected_items = []
        select_rect = self._start_pos, self._end_pos
        for i in self.component.items:

            if self.component.check_collision(i, select_rect):
                i.selected = True
                self.component.selected_items.append(i)
            else:
                i.selected = False

    def normal_key_pressed(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        if event.character == 'z':
            self._enabled = not self._enabled
            event.handled = True

    def normal_left_down(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        if self._enabled:
            self._start_select(event)
            event.handled = True

    def selecting_mouse_move(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        self._end_pos = (event.x, event.y)
        self.component.request_redraw()
        event.handled = True

    def selecting_left_up(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        self._end_select(event)

    def overlay(self, component, gc, *args, **kw):
        '''
            @type component: C{str}
            @param component:

            @type gc: C{str}
            @param gc:

            @type *args: C{str}
            @param *args:

            @type **kw: C{str}
            @param **kw:
        '''
        with gc:
            if self._start_pos and self._end_pos:
                x, y = self._start_pos
                x2, y2 = self._end_pos
                rect = (x, y, x2 - x + 1, y2 - y + 1)
                gc.set_fill_color([1, 0, 0, 0.5])
                gc.set_stroke_color([1, 0, 0, 0.5])
                gc.rect(*rect)
                gc.draw_path()
#============= views ===================================
#============= EOF ====================================
