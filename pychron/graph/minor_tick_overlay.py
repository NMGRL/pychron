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
from traits.api import Float, Int, Bool, Enum, Any
from chaco.abstract_overlay import AbstractOverlay
from chaco.ticks import auto_ticks

# ============= standard library imports ========================

# ============= local library imports  ==========================


class MinorTicksOverlay(AbstractOverlay):
    tick_in = Float(2.5)
    tick_out = Float(2.5)
    interval = Int(5)
    use_endpoints = Bool(True)
    orientation = Enum('v', 'h')
    placement = Enum('normal', 'opposite')
    aux_component = Any

    def overlay(self, component, gc, *args, **kw):
        '''
        :param: component
        '''
        try:
            gc.save_state()
            c = self.component
#            print c, component
            if self.aux_component is not None:
                component = self.aux_component
#                print 'axu', component

            if self.orientation == 'v':
                r = c.index_range
                nt = len(component.x_axis.ticklabel_cache)
            else:
                r = c.value_range
                nt = len(component.y_axis.ticklabel_cache)

            s = r.low
            e = r.high

            ts = auto_ticks(s, e, s, e, (nt + 2) * -self.interval, use_endpoints=self.use_endpoints)
            for ti in ts:

                if self.orientation == 'v':
                    ti = round(c.map_screen([[ti, 0]])[0][0])
                    if self.placement == 'normal':
                        y = c.y
                    else:
                        y = c.y2 + 1
#                    print y
                    args1 = ti, y - self.tick_in
                    args2 = ti, y + self.tick_out
                else:
                    ti = round(c.map_screen([[0, ti]])[0][1])
                    if self.placement == 'normal':
                        x = component.x
                    else:
                        x = component.x2

                    args1 = x - self.tick_out, ti
                    args2 = x + self.tick_in, ti

                gc.move_to(*args1)
                gc.line_to(*args2)

            gc.stroke_path()

        except Exception, e:
            print 'exception', e
        finally:
            gc.restore_state()

# ============= EOF =====================================
