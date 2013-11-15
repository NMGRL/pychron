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
from traits.api import HasTraits, Range, Instance, Property
from traitsui.api import View, Item, Group

#============= standard library imports ========================
from numpy import linspace

#============= local library imports  ==========================

from pychron.graph.graph import Graph
from pychron.hardware.core.motion.motion_profiler import MotionProfiler


class MotionDesigner(HasTraits):
    canvas = Instance(Graph)

    acceleration = Property(Range(0, 8., 7.62), depends_on='_acceleration')
    _acceleration = Range(0, 8., 7.62)
    # deceleration = Range(0, 8., 7.62)
    velocity = Property(Range(0, 8., 3.81), depends_on='_velocity')
    _velocity = Range(0, 8., 3.81)

    distance = Property(Range(0, 10., 5), depends_on='_distance')
    _distance = Range(0, 10., 5)
#    beam_radius = Range(0, 1.5, 1)

    def _set_velocity(self, v):
        self._velocity = v

    def _set_distance(self, d):
        self._distance = d
        mp = MotionProfiler()
        cv, ac, dc = mp.calculate_corrected_parameters(self.distance, self.velocity, self.acceleration, self.acceleration)
        times, dist = mp.calculate_transit_parameters(self.distance, cv, ac, dc)
        self._acceleration = ac
        self._velocity = cv
        self.plot_velocity_profile(times, cv, 0)
        self.plot_position_profile(*times)

    def _set_acceleration(self, a):
        self._acceleration = a

    def _get_velocity(self):
        return self._velocity

    def _get_distance(self):
        return self._distance

    def _get_acceleration(self, a):
        return self._acceleration

#    def _anytrait_changed(self, name, old, new):
#        if name in ['acceleration', 'deceleration', 'velocity',
#            #        'distance',
#                    #'beam_radius'
#                    ]:
#            self.replot()
#        elif name in ['distance']:
#            mp=MotionProfiler()
#            cv,ac,dc=mp.calculate_corrected_parameters(self.distance, self.velocity, self.acceleration, self.acceleration)
#            times, dist=mp.calculate_transit_parameters(self.distance, cv, ac, dc)
#
#            self.plot_velocity_profile(times,cv, 0)
#            self.plot_position_profile(*times, 1)

    def replot(self):
        g = self.canvas

        g.clear()
        g.new_plot(title='Velocity')
        g.new_plot(title='Position')

        atime, dtime, vtime = self.velocity_profile(0)

        self.plot_position_profile(atime, dtime, vtime, 1)

    def plot_position_profile(self, atime, dtime, vtime, ploitid=1):
        g = self.canvas

        x = [0]
        y = [0]
        # plot accel
        for i in linspace(0, atime, 50):
            x.append(i)

            p = 0.5 * self.acceleration * i ** 2
            y.append(p)

        # plot constant velocity
        yo = p + vtime * self.velocity

        # plot decel
        for i in linspace(0, dtime, 50):
            x.append(atime + vtime + i)
#            p = yo + self.velocity * i - 0.5 * self.deceleration * i ** 2
            p = yo + self.velocity * i - 0.5 * self.acceleration * i ** 2
            y.append(p)
        g.new_series(x, y, render_style='connectedpoints')

        # plot beam center
#        y = [p / 2.0] * 50
#        x = linspace(0, atime + vtime + dtime, 50)
#        g.new_series(x, y)

        # plot beam radius'
        # include padding in the beam radius
        # yl = [pi - self.beam_radius for pi in y]
        # yu = [pi + self.beam_radius for pi in y]
        # g.new_series(x, yl, color='blue')
        # g.new_series(x, yu, color='blue')

    def velocity_profile(self, plotid):

#        v = self.velocity
        # ac = self.acceleration
        # dc = self.deceleration

        d = self.distance
        m = MotionProfiler()

        times, dists = m.calculate_transit_parameters(d, self.velocity,
                                                         self.acceleration,
                                                       self.acceleration)
        self.plot_velocity_profile(times, self.velocity, plotid)
        return times

    def plot_velocity_profile(self, times, v, plotid):
        g = self.canvas
        atime, dtime, vtime = times
        # error, atime, dtime, cvd = m.check_motion(v, ac, d)
        x = [0]
        y = [0]

#        atime = v / float(ac)
#        dtime = v / float(dc)
        x.append(atime)
        y.append(v)

#        acd = 0.5 * ac * atime ** 2
#        dcd = 0.5 * ac * dtime ** 2
#
#        cvd = d - acd - dcd
#
#        if cvd < 0:
#            #calculate a corrected velocity
#            vc = math.sqrt((2 * d * ac) / 3.)
#            print vc

        x.append(atime + vtime)
        y.append(v)
#
        totaltime = atime + dtime + vtime
        x.append(totaltime)
        y.append(0)
        g.new_series(x, y, plotid=plotid, render_style='connectedpoints')
        g.set_y_limits(plotid=plotid, max_=self.velocity + 5)

        return atime, dtime, vtime

#============= views ===================================
    def traits_view(self):
        cgrp = Group(
                   Item('acceleration'),
                 #  Item('deceleration'),
                   Item('velocity'),
                   Item('distance'),
                  # Item('beam_radius')
                   )
        v = View(
                 cgrp,
                 Item('canvas', show_label=False,
                    style='custom'),
                 resizable=True,
                 width=800,
                 height=700
                 )
        return v

    def _canvas_default(self):
        g = Graph()

        return g


if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    logging_setup('motionprofiler')
    m = MotionDesigner()
    m.replot()
    m.configure_traits()
#============= EOF ====================================
