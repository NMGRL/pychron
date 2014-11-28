# ===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
from traits.api import Float

from pychron.config_loadable import ConfigLoadable

#============= standard library imports ========================
import math
import os
#============= local library imports  ==========================

class MotionProfiler(ConfigLoadable):
    velocity_tol = Float(0.5)
    acceleration_tol = Float(0.5)
    deceleration_tol = Float(0.05)

    max_velocity = Float(4)
    min_velocity = Float(0.05)

    min_acceleration = Float(0.05)
    min_deceleration = Float(0.05)

    min_acceleration_time = Float(0.2)
    max_transit_time = Float(5)
    max_acceleration = Float(50)

    def load(self, p):
        attrs = ['max_velocity', 'max_transit_time',
               'min_acceleration_time', 'velocity_tol',
               'acceleration_tol', 'deceleration_tol',
               'max_acceleration'
               ]
        self.config_path = p
        if os.path.isfile(p):
            config = self.get_configuration(self.config_path)
            for attr in attrs:
                self.set_attribute(config, attr, 'General', attr, cast='float')
        else:
            # create a new config file with default values
            config = self.configparser_factory()
            config.add_section('General')
            for attr in attrs:
                config.set('General', attr, getattr(self, attr))
            self.write_configuration(config)

    def check_motion(self, displacement, obj):
#         ac = obj.nominal_acceleration
#         dc = obj.nominal_deceleration
#         v = obj.nominal_velocity

        mv = obj.velocity
        mac = obj.acceleration
        mdc = obj.deceleration

        try:
            nv, nac, ndc = self.calculate_corrected_parameters(0,
                                                               displacement, mac, mdc)
        except Exception:
            '''
                max recusion.
                
                max velocity prevents move of this displacement
                from taking less than max transit time
                
                use max velocity and nominal acc. 
            '''
            nv, nac, ndc = self.max_velocity, obj.nominal_acceleration, obj.nominal_deceleration


        dv = abs(nv - mv)
        dac = abs(nac - mac)
        ddc = abs(ndc - mdc)
        change = (
                  dv / mv > self.velocity_tol or
                  dac / mac > self.acceleration_tol or
                  ddc / mdc > self.deceleration_tol)

        return change, nv, max(0.1, nac), max(0.1, ndc)

    def calculate_corrected_parameters(self, cnt, displacement, acc, dec):

        vel = (displacement * 2 * acc / 3.) ** 0.5
        vel = min(self.max_velocity, vel)

        if cnt > 200 or \
             acc >= self.max_acceleration or \
                 dec >= self.max_acceleration:
            acc = min(acc, self.max_acceleration)
            dec = min(dec, self.max_acceleration)
            return vel, acc, dec

        # do current parameters define trapezoidal move
        times, _ = self.calculate_transit_parameters(displacement,
                                                    vel, acc, dec)
#         print cnt, '---------------------------'
#         print 'times', times

        # if all times are greater than 0 then trapezoid
        if all([ti >= 0 for ti in times]):
#             print 'is trapezoid'
            # is time greater than max transit time
            if sum(times) > self.max_transit_time:
                '''
                    this move takes too long. 
                    use max velocity and increase acc until this is a trapezoidal 
                    move
                '''


#                 print 'max transit', sum(times)
                return self.calculate_corrected_parameters(cnt + 1,
                                                           displacement,
                                                           acc * 1.01, dec * 1.01)

#             # is ac time less than min
            if times[0] < self.min_acceleration_time or \
                 times[1] < self.min_acceleration_time:
                '''
                    acc is too fast. calculate new accel so that acctime=min
                '''
                ac = vel / (2 * self.min_acceleration_time)
                return self.calculate_corrected_parameters(cnt + 1,
                                                           displacement,
                                                           ac, ac
                                                           )
            return vel, acc, dec

        else:  # not a trapezoid
            '''
                velocity time is negative. 
                increace acc and dec. this reduces acctime, increasing veltime
            '''
            return self.calculate_corrected_parameters(cnt + 1,
                                                       displacement,
                                                       acc * 1.01, dec * 1.01)

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

        return (atime, dtime, cvtime), (acd, dcd, cvd)

# def _new_velocity(self, displacement, oac, odc):
#         ac, dc = float(oac), float(odc)
#         acdc_param = 1 / ac + 1 / dc
#         A = 0.5 * acdc_param
#         B = -self.max_transit_time
#         C = displacement
#         det = B ** 2 - 4 * A * C
#
#         i = 1
#         p = 0.01
#         while det < 0:
# #             ac *= 1.01
# #             dc *= 1.01
#             ac = oac * (1 + p * i)
#             dc = odc * (1 + p * i)
#             acdc_param = 1 / ac + 1 / dc
#
#             A = 0.5 * acdc_param
#             det = B ** 2 - 4 * A * C
#             if i > 1000:
#                 p += 0.01
#             i += 1
#
#         cv = (-B + math.sqrt(B ** 2 - 4 * A * C)) / (2 * A)
#         return cv
# ============= EOF =============================================
