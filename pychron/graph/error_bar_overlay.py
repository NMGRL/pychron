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



#=============enthought library imports=======================
from traits.api import Int, Enum
from chaco.api import AbstractOverlay
from enable.colors import color_table
#============= standard library imports ========================

from numpy import column_stack, transpose, invert, isnan, compress, arange, ma, delete
#============= local library imports  ==========================


class ErrorBarOverlay(AbstractOverlay):
    orientation = Enum('x', 'y')

    draw_layer = 'underlay'
    nsigma = 1
    _cache_valid = False

    def overlay(self, component, gc, view_bounds, mode='normal'):
        with gc:
            gc.clip_to_rect(component.x, component.y,
                            component.width, component.height)

            comp = self.component
            x = comp.index.get_data()
            y = comp.value.get_data()

            if self.orientation == 'x':
                y = comp.value_mapper.map_screen(y)
                err = comp.xerror.get_data()

                err = err * self.nsigma
                xlow, xhigh = x - err, x + err
                xlow = comp.index_mapper.map_screen(xlow)
                xhigh = comp.index_mapper.map_screen(xhigh)

                start, end = column_stack((xlow, y)), column_stack((xhigh, y))
            else:
                x = comp.index_mapper.map_screen(x)
                err = comp.yerror.get_data()

                err = err * self.nsigma
                ylow, yhigh = y - err, y + err
                ylow = comp.value_mapper.map_screen(ylow)
                yhigh = comp.value_mapper.map_screen(yhigh)
                #                 idx = arange(len(x))
                start, end = column_stack((x, ylow)), column_stack((x, yhigh))


            #            sels = (a for i, a in enumerate(zip(args1, args2)) if i in sel)
            #            nonsels = (a for i, a in enumerate(zip(args1, args2)) if i not in sel)
            #            sel = comp.index.metadata.get('selections', [])
            #            if sel:
            #                nonsel = arange(len(x))
            #                nonsel = delete(nonsel, sel)
            #                sel_start, sel_end = start[sel], end[sel]
            #                start, end = start[nonsel], end[nonsel]
            #                color = (1, 0, 0)
            #                # draw selected
            #                gc.set_stroke_color(color)
            #                gc.set_fill_color(color)
            #                gc.line_set(sel_start, sel_end)
            #                gc.draw_path()


            # draw normal
            color = component.color
            if isinstance(color, str):
                color = color_table[color]
                #print 'ebo color',color
            gc.set_stroke_color(color)
            gc.set_fill_color(color)
            gc.line_set(start, end)
            gc.draw_path()


#============= EOF =====================================
