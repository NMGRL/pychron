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
from traits.api import Property, Instance, DelegatesTo
# from traitsui.api import View, Item, Group, HGroup, VGroup
from traitsui.api import VGroup, Item, HGroup

#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.hardware.agilent_dac import AgilentDAC
from pychron.led.led_editor import LEDEditor
from pychron.hardware.actuators.agilent_gp_actuator import AgilentGPActuator
from pychron.lasers.laser_managers.laser_manager import LaserManager

class SynradCO2Manager(LaserManager):
    name = 'SynradCO2'

    control_dac = Instance(AgilentDAC)
    control_switch = Instance(AgilentGPActuator)
    request_power = Property(depends_on='control_dac.value')
    request_powermin = DelegatesTo('control_dac', prefix='min_value')
    request_powermax = DelegatesTo('control_dac', prefix='max_value')

    enable_address = 120

    def _get_request_power(self):
        return self.control_dac.value

    def _set_request_power(self, v):
        self.set_laser_power(v)

    def set_laser_power(self, v):
        self.control_dac.set(v)

    def disable_laser(self):

        self.control_switch.close_channel(self.enable_address)
        super(SynradCO2Manager, self).disable_laser()

        return True

    def enable_laser(self):
        '''
        '''

        is_ok = True

        self.control_switch.open_channel(self.enable_address)

        super(SynradCO2Manager, self).enable_laser(is_ok=is_ok)


        return is_ok

    def _control_dac_default(self):
        return AgilentDAC(name='control_dac',
                          configuration_dir_name='synrad',
                          )
    def _control_switch_default(self):
        a = AgilentGPActuator(name='control_switch',
                          configuration_dir_name='synrad',
                          )


        return a


    def __control__group__(self):
        '''
        '''
        l = 'CO2'
        vg = VGroup(show_border=True, label='%s Laser' % l)

        vg.content.append(HGroup(
                                 Item('enabled_led', show_label=False, style='custom', editor=LEDEditor()),
                                 self._button_group_factory(self.get_control_buttons(), orientation='h'))
                                 )

        ps = self.get_power_slider()
        if ps:
            vg.content.append(ps)

        # vg.content.append(Item('light_intensity', enabled_when = 'fiber_light.state'))

        citems = self.get_control_items()
        if citems:
            vg.content.append(citems)

        ac = self.get_additional_controls()
        if ac:
            vg.content.append(ac)

        return vg

    def _stage_manager_default(self):
        '''
        '''

        args = dict(name='synradstage',
                            configuration_dir_name='synrad',
                             parent=self)
        stm = self._stage_manager_factory(args)

        return stm
#============= views ===================================
#============= EOF ====================================
