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
from traits.api import Float, Bool, on_trait_change
from traitsui.api import View, Item, Group, HGroup, spring
#============= standard library imports ========================
import math
from pychron.config_loadable import ConfigLoadable
import os
#============= local library imports  ==========================

ATTRS = ['max_velocity', 'max_transit_time',
'min_acceleration_time', 'velocity_tol',
'acceleration_tol', 'deceleration_tol'
]


class MotionProfiler(ConfigLoadable):
#===========================================================================
# configable parameters
#===========================================================================
    velocity_tol = Float(0.5, enter_set=True, auto_set=False)
    acceleration_tol = Float(0.5, enter_set=True, auto_set=False)
    deceleration_tol = Float(0.05, enter_set=True, auto_set=False)

    max_velocity = Float(4, enter_set=True, auto_set=False)
    min_velocity = Float(0.05, enter_set=True, auto_set=False)

    min_acceleration = Float(0.05)
    min_deceleration = Float(0.05)

    min_acceleration_time = Float(0.2, enter_set=True, auto_set=False)
    max_transit_time = Float(5, enter_set=True, auto_set=False)
#===============================================================================
# computed parameters
#===============================================================================
    atime = Float
    dtime = Float
    cvtime = Float

    adisp = Float
    ddisp = Float
    cvdisp = Float

#===============================================================================
# error flags
#===============================================================================
    max_transit_err = Bool
    velocity_err = Bool
    min_acceleration_err = Bool
    trapezoidal_err = Bool

    @on_trait_change(','.join(ATTRS))
    def save_parameter(self, obj, name, old, new):

        config = self.get_configuration(self.config_path)
        config.set('General', name, new)
        self.write_configuration(config, self.config_path)

    def load(self, p):
        self.config_path = p
        if os.path.isfile(p):
            config = self.get_configuration(self.config_path)
            for attr in ATTRS:
                self.set_attribute(config, attr, 'General', attr, cast='float')
        else:
            # create a new config file with default values
            config = self.configparser_factory()
            config.add_section('General')
            for attr in ATTRS:
                config.set('General', attr, getattr(self, attr))
            self.write_configuration(config)

    def traits_view(self):
        v = View(
                Group(
                    Item('velocity_tol'),
                    Item('acceleration_tol'),
                    Item('deceleration_tol'),
                    Item('min_velocity'),
                    Item('max_velocity'),
                    Item('max_transit_time'),
                    Item('min_acceleration_time'),
                    label='Tolerances'
                     ),
                 Group(
                       HGroup(
                               Group(
                                     Item('atime', format_str='%0.4f', style='readonly'),
                                     Item('dtime', format_str='%0.4f', style='readonly'),
                                     Item('cvtime', format_str='%0.4f', style='readonly'),
                                     ),
                               spring,
                               Group(
                                     Item('adisp', format_str='%0.4f', style='readonly'),
                                     Item('ddisp', format_str='%0.4f', style='readonly'),
                                     Item('cvdisp', format_str='%0.4f', style='readonly'),
                                     )
                              ),
                       Group(
                             Item('max_transit_err', style='custom'),
                             Item('velocity_err', style='custom'),
                             Item('min_acceleration_err', style='custom'),
                             Item('trapezoidal_err', style='custom'),
                             ),
                       label='Results'
                       )
               )
        return v

    def check_motion(self, displacement, obj):
        ac = obj.nominal_acceleration
        dc = obj.nominal_deceleration
        v = obj.nominal_velocity

        mv = obj.velocity
        mac = obj.acceleration
        mdc = obj.deceleration

        nv, nac, ndc = self.calculate_corrected_parameters(displacement, v, ac, dc)
        dv = abs(nv - mv)
        dac = abs(nac - mac)
        ddc = abs(ndc - mdc)
        change = (
                  dv / mv > self.velocity_tol or
                  dac / mac > self.acceleration_tol or
                  ddc / mdc > self.deceleration_tol)
        return change, nv, max(0.1, nac), max(0.1, ndc)

    def calculate_transit_parameters(self, displacement, v, ac, dc):
        '''
            return the time spent accelerating, decelerating, and at speed
            and respective displacements
        '''
        # time to velocity
        atime = v / ac
        dtime = v / dc

        # acceleration distance
        acd = 0.5 * ac * math.pow(atime, 2)

        # decel distance
        dcd = 0.5 * dc * math.pow(dtime, 2)

        # constant velocity distance
        cvd = displacement - acd - dcd

        cvtime = cvd / v

        self.atime = atime
        self.dtime = dtime
        self.cvtime = cvtime

        self.adisp = acd
        self.ddisp = dcd
        self.cvdisp = cvd

        return (atime, dtime, cvtime), (acd, dcd, cvd),


    def calculate_corrected_parameters(self, displacement, velocity, ac, dc):
        self.velocity_err = False
        self.min_acceleration_err = False
        self.max_transit_err = False
        self.trapezoidal_err = False
        ac = float(ac)
        dc = float(dc)
#        force = False
        acdc_param = 1 / ac + 1 / dc
        '''
            trapezodail movement
            calculate velocity so that atime=dtime=1/2vtime
        '''

        cv = (displacement * ac / 2.0) ** 0.5
        times, _distances = self.calculate_transit_parameters(displacement, cv, ac, dc)

        oac = ac
        odc = dc
        if sum(times) > self.max_transit_time:
            self.max_transit_err = True
            self.debug('max transit error. {} > {}'.format(sum(times), self.max_transit_time))
            # calculate the min velocity required for max_transit_time
            # given ac and dc
            A = 0.5 * acdc_param
            B = -self.max_transit_time
            C = displacement
            det = B ** 2 - 4 * A * C
            while det < 0:
                ac *= 1.01
                dc *= 1.01
                acdc_param = 1 / ac + 1 / dc
                A = 0.5 * acdc_param
                B = -self.max_transit_time
                C = displacement
                det = B ** 2 - 4 * A * C

#             A = 0.5 * acdc_param
#             B = -self.max_transit_time
#             C = displacement
#             det = B ** 2 - 4 * A * C
#
#             i = 1
#             p = 0.01
#             while det < 0:
#                 ac = oac * (1 + p * i)
#                 dc = odc * (1 + p * i)
#                 acdc_param = 1 / ac + 1 / dc
#
#                 A = 0.5 * acdc_param
#                 det = B ** 2 - 4 * A * C
#                 if i > 1000:
#                     p += 0.01

            cv = (-B + math.sqrt(B ** 2 - 4 * A * C)) / (2 * A)

        cv = min(self.max_velocity, cv)

        if times[0] < self.min_acceleration_time:
            self.min_acceleration_err = True
#            #calculate new acceleration for fixed accel time
            ac = cv / self.min_acceleration_time
            self.debug('minimum acceleration time err. {} > {} new accel= {}'.format(times[0],
                                                                                     self.min_acceleration_time, ac))
            dc = ac
#            cv = self.min_acceleration_time * ac
            times, _distances = self.calculate_transit_parameters(displacement, cv, ac, dc)

            if _distances[2] < 0:
                self.trapezoidal_err = True
                ac = displacement / (2 * self.min_acceleration_time ** 2)
                dc = ac
                ncv = ac * self.min_acceleration_time

                self.debug('trapezoidal err. negative velocity displacement velocity= {} new velocity= {}'.format(cv, ncv))
                cv = ncv

#                cv = self.min_velocity
#                ac = self.min_acceleration
#                dc = self.min_acceleration
                # ncv, ac, dc = self.find_min(displacement, cv, ac, dc)
#            force = True

#            times, _distances = self.calculate_transit_parameters(displacement, cv, ac, dc)
        return cv, ac, dc

#    def find_min(self, disp, v, a, d, tol=0.001):
#
#        times, _distances = self.calculate_transit_parameters(disp, v, a, d)
#        _atime = times[0]
#        _cvtime = times[2]


#        if abs(atime - cvtime) < tol:
#            return v, a, d
#        else:
#            v = v * 0.99
#            a = v / self.min_acceleration_time
#            d = a
#            try:
#                np = self.find_min(self, disp, v, a, d)
#            except RuntimeError, e:
#                print e, v, a, d
#                np = self.min_velocity, self.min_acceleration. self.min_deceleration
#            return np

if __name__ == '__main__':
    m = MotionProfiler()
    a = 5
    d = 5
    v = 3.

    disp = 0.01
    print 'calc parameters', m.calculate_corrected_parameters(disp, v, a, d)

#============= EOF ====================================
