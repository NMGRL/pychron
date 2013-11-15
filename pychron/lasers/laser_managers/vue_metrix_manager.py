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
from traits.api import Instance
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.hardware.fusions.vue_diode_control_module import VueDiodeControlModule



class VueMetrixManager(Manager):

    control = Instance(VueDiodeControlModule)
    timer = None
#    def _update_(self):
#
#        a = self.read_laser_amps(verbose = False)
#        if a is not None:
#            self.laser_amps = a
#        t = self.get_internal_temperature(verbose = False)
#        if t is not None:
#            self.laser_temperature = t
#
#        p = self.read_measured_power(verbose = False)
#        if p is not None:
#            self.laser_power = p
#
#        v = self.read_laser_voltage_adc(verbose = False)
#        if v is not None:
#            self.laser_voltage = v

    def __getattr__(self, attr):

        if hasattr(self.control, attr):
            obj = self.control
            return getattr(obj, attr)
        else:
            raise AttributeError(attr)

#    def start_scan(self):
#        self.control.start_scan()

#    def opened(self):
#        self.start()

#    def finish_loading(self):
#        super(VueMetrixManager, self).finish_loading()
#        if self.is_scanable:
#            self.start_scan()

    def _control_default(self):
        '''
        '''
        b = VueDiodeControlModule(name='vue_metrix_controlmodule',
                                      configuration_dir_name='fusions_diode'
                                      )
        return b

#============= views ===================================
    def traits_view(self):
        v = View(
                 Item('control', show_label=False, style='custom'),
#                 VGroup(
#                        Item('laser_amps', format_str = '%0.2f', style = 'readonly'),
#                        Item('laser_temperature', format_str = '%0.2f', style = 'readonly'),
#                        Item('laser_power', format_str = '%0.2f', style = 'readonly'),
#                        Item('laser_voltage', format_str = '%0.2f', style = 'readonly'),
#                        ),
#                    handler = self.handler_klass,
                    width=500,
                    height=500,
                    resizable=True
                 )
        return v



if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    logging_setup('vue_metrix')
    v = VueMetrixManager()
    v.control.bootstrap()
    v.configure_traits()

#============= EOF ====================================
