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



# ============= enthought library imports =======================
from traits.api import Int, Enum, CFloat
from traitsui.api import View, Item, Group

# ============= standard library imports ========================
# import math
# ============= local library imports  ==========================
from pychron.hardware.axis import Axis

yes_no = Enum('yes', 'no')

class AerotechAxis(Axis):
    id = Int

    home_direction_ccw = yes_no
    home_switch_normally_open = yes_no
    home_feedrate = CFloat
    home_offset = CFloat
    limit_switch_normally_open = yes_no
    def load(self, path):
        for key, value in self._get_parameters(path):
#            if key in ['sign']:
#                value = int(value)
            setattr(self, key, value)

    def _validate_velocity(self, v):
        return self._validate_float(v)

    def _set_velocity(self, v):
        self.nominal_velocity = v
        self.trait_set(_velocity=v, trait_change_notify=False)

    def load_parameters(self):

        # homing and limts 4.7
        attrs = [
                    ('home_direction_ccw', 2),
                    ('home_switch_normally_open', 3),
                    ('home_feedrate', 4),
                    ('home_offset', 6), ]
        attrs += [
                    ('limit_switch_normally_open', 9),
                    ('limit_to_mechanical_stop', 10),
                    ('ccw_software_limit', 22),
                    ('cw_software_limit', 23), ]
        attrs += [
                    ('position_channel', 38),
                    ('velocity_channel', 39),
                    ('position_setup_code', 40),
                    ('velocity_setup_code', 41),
                    ('amplifier_type', 42),
                    ('commutation_cycles_per_rev', 43),
                    ('feedback_steps_per_rev', 44),
                    ('commutation_phase_offset', 45),
                    ('stepper_high_current', 46),
                    ('stepper_low_current', 47),
                    ('microstepping_resolution', 63),
                    ('stepper_correction', 64),
                    ('stepper_correction_speed', 65),
                    ('base_speed', 66),
                    ('base_speed_advance', 67),
                    ('phase_speed', 68),
                    ('phase_speed_advance', 69),
                    ('primary_dac_offset', 79),
                    ('secondary_dac_offset', 80),
                    ('encoder_factor', 82), ]
        attrs += [
                    ('global_fault_mask', 55),
                    ('disable', 56),
                    ('interrupt', 57),
                    ('aux_output', 58),
                    ('halt_queue', 59),
                    ('abort_motion', 60),
                    ('enable_brake', 61),
                ]

        attrs += [
                    ('top_feedrate', 17),
                    ('maximum_velocity_error', 18),
                    ('maximum_position_error', 19),
                    ('maximum_integral_error', 20),
                    ('rms_current_trap', 48),
                    ('rms_current_sample_time', 49),
                    ('clamp_current_output', 53),
                    ('aux_fault_output_bit', 54),
                    ('amplifier_fault_active_low', 70)
                ]
        param_table = []
        for name, code in attrs:
            cmd = self._build_query(code)
            rp = self.ask(cmd)
            if rp is not None:
                rp = rp.strip()
                try:
                    setattr(self, name, rp)
                    param_table.append(rp)
                except Exception:
                    self.warning('{} not set invalid value {}'.format(name, rp))


        names, codes = zip(*attrs)
        return names, codes, param_table

    def _build_query(self, code):
        cmd = 'RP{}{:02}'.format(self.id, code)
        return cmd

    def simple_view(self):
        home_grp = Group(Item('home_direction_ccw'),
                 Item('home_switch_normally_open'),
                 Item('home_feedrate'),
                 Item('home_offset'),
                 label='Home')

        limits_grp = Group(Item('limit_switch_normally_open'),
                        label='Limits')
        v = View(Item('id', style='readonly'),
                 home_grp,
                 limits_grp,

                 )

        return v

# class AerotechAxis(Axis):
#    '''
#    '''
#    feedrate = Float(enter_set=True, auto_set=False)
#    metric_digits = Int
#    mlow = Int(1)
#    mhigh = Int(8)
#
#    conversion_factor = Float(enter_set=True, auto_set=False)
#
#    rms_current_sample_time = Property(Float(enter_set=True, auto_set=False))
#    _rms_current_sample_time = Float
#
#    def _validate_rms_current_sample_time(self, s):
#        '''
#
#        '''
#        if 0 <= s <= 16383:
#            nv = s
#        else:
#            nv = self._rms_current_sample_time
#        return nv
#
#    def _get_rms_current_sample_time(self):
#        '''
#        '''
#        return self._rms_current_sample_time
#
#    def _set_rms_current_sample_time(self, v):
#        '''
#
#        '''
#        cmd = int('%i49' % self.id)
#        self.parent.set_parameter(cmd, v)
#
# #    def load_parameters_from_config(self, path):
# #        '''
# #
# #        '''
# #        for key, value in self._get_parameters(path):
# #            pass
#
#    def load_parameters_from_device(self):
#        '''
#        '''
#        if not self.parent.simulation:
#            params = ['feedrate', (23, 24, 25, 26)]
#            for p, pn in params:
#                cmd = 'RP{}'
#                n = pn
#                if isinstance(pn, tuple):
#                    n = pn[self.id - 1]
#                cmd = cmd.format(n)
#
#                self.parent.ask(cmd)
#                value = 0
#                setattr(p, value)
#
#    def _feedrate_changed(self):
#        '''
#        '''
#        n = (23, 24, 25, 26)[self.id - 1]
#        self._set_parameter(n, self.feedrate)
#
#    def _metric_digits_changed(self):
#        '''
#        '''
#        n = (29, 47, 65, 83)[self.id - 1]
#
#        self._set_parameter(n, self.metric_digits)
#
#    def _conversion_factor_changed(self):
#        '''
#        '''
#        n = int('%i00' % self.id)
#        v = self.conversion_factor
#
# #        machine_steps = 4000
# #        prog_unit = 10
# #
# #        cf = (machine_steps / prog_unit) / math.pow(10, self.metric_digits)
#
#        self._set_parameter(n, v)
#
#    def _set_parameter(self, n, v):
#        '''
#
#        '''
#        self.parent.set_parameter(n, v)
#
#    def _anytrait_changed(self, name, old, new):
#        '''
#
#        '''
#        #print name,old,new
#        pass
#
#    def traits_view(self):
#        '''
#        '''
#        axis_config = Group(Item('conversion_factor'))
#        planes = Group(Item('feedrate'),
#                     Item('metric_digits', editor=RangeEditor(mode='spinner',
#                                                             low_name='mlow',
#                                                             high_name='mhigh')))
#        traps = Group(Item('rms_current_sample_time'))
#        return View(axis_config,
#                    planes,
#                    traps,
#                    )
# ============= EOF ====================================
