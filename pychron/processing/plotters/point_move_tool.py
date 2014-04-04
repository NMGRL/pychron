#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from enable.enable_traits import Pointer
from traits.api import Enum, CArray
from chaco.tools.api import DragTool
#============= standard library imports ========================
#============= local library imports  ==========================
normal_pointer = Pointer('normal')
hand_pointer = Pointer('hand')


class PointMoveTool(DragTool):
    event_state = Enum("normal", "dragging")
    _prev_pt = CArray
    constrain = Enum(None, 'x', 'y')
    def is_draggable(self, x, y):
        return self.component.hittest((x, y))

    def drag_start(self, event):
        data_pt = self.component.map_data((event.x, event.y), all_values=True)
        self._prev_pt = data_pt
        event.handled = True

    def dragging(self, event):
        plot = self.component
        cur_pt = plot.map_data((event.x, event.y), all_values=True)
        dy = cur_pt[1] - self._prev_pt[1]
        dx = cur_pt[0] - self._prev_pt[0]


        if self.constrain == 'x':
            dy = 0
        elif self.constrain == 'y':
            dx = 0

        index = plot.index.get_data() + dx
        value = plot.value.get_data() + dy

        pad = 10  # pixel boundary

        xy = plot.map_data((0, 0), all_values=True)
        xy2 = plot.map_data((pad, pad), all_values=True)
        if self.constrain == 'y':
            dd = xy2[1] - xy[1]
            value[value < dd] = dd
            h = plot.map_data((0, plot.y2 - pad), all_values=True)[1]
            value[value > h] = h
        elif self.constrain == 'x':
            dd = xy2[0] - xy[0]
            index[index < dd] = dd
            w = plot.map_data((plot.x2 - pad, 0), all_values=True)[1]
            index[value > w] = w

        # move the point
        plot.index.set_data(index, sort_order=plot.index.sort_order)
        plot.value.set_data(value, sort_order=plot.value.sort_order)

        self._prev_pt = cur_pt
        event.handled = True
        plot.request_redraw()


class OverlayMoveTool(PointMoveTool):
    def is_draggable(self, x, y):
        return self.component.hittest((x, y))

    def drag_end(self, event):
        event.window.set_pointer('arrow')

    def drag_start(self, event):
        event.window.set_pointer('hand')
        data_pt = self.component.get_current_point()
        #data_pt = self.component.map_data((event.x, event.y), all_values=True)
        self._prev_pt = data_pt
        event.handled = True

    def dragging(self, event):
        curp = self.component.get_current_point()
        if self.constrain == 'x':
            ax, ay = curp[0], event.y
        elif self.constrain == 'y':
            ax, ay = event.x, curp[1]
        else:
            ax, ay = event.x, event.y

        self.component.altered_screen_point = ax, ay
        self._prev_pt = (event.x, event.y)
        self.component.request_redraw()
        event.handled = True


class LabelMoveTool(OverlayMoveTool):
    def drag_start(self, event):
        event.window.set_pointer('hand')
        x, y = self.component.get_current_point()
        self._offset = (event.x - x, event.y - y)
        event.handled = True

    def dragging(self, event):
        comp = self.component
        if not event.handled:
            # x, y = self.component.get_current_point()
            sx, sy = event.x, event.y
            ox, oy = self._offset
            comp.trait_set(x=sx - ox, y=sy - oy)
            comp.set_altered()
        comp.request_redraw()
        event.handled = False

    #============= EOF =============================================
