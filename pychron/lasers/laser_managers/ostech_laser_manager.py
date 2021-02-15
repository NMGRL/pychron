# ===============================================================================
# Copyright 2020 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from traitsui.api import UCustom, UItem, VGroup, InstanceEditor
from traits.api import Instance
from pychron.hardware.fiber_light import FiberLight
from pychron.hardware.ostech import OsTechLaserController
from pychron.lasers.laser_managers.laser_manager import LaserManager
from pychron.lasers.laser_managers.pyrometer_mixin import PyrometerMixin
from pychron.lasers.laser_managers.watlow_mixin import WatlowMixin


class OsTechLaserManager(LaserManager):
    laser_controller = Instance(OsTechLaserController)

    def _laser_controller_default(self):
        return OsTechLaserController(name='laser_controller',
                                     configuration_name='laser_controller',
                                     configuration_dir_name=self.configuration_dir_name)


class OsTechDiodeManager(OsTechLaserManager, WatlowMixin, PyrometerMixin):
    stage_manager_id = 'ostech.diode'
    configuration_dir_name = 'ostech_diode'
    stage_controller_klass = 'Zaber'
    fiber_light = Instance(FiberLight)

    def _enable_hook(self):
        if super(OsTechDiodeManager, self)._enable_hook():
            # logic board successfully enabled
            # disable the temperature_controller unit a value is set
            self.temperature_controller.disable()

            return True

    def _disable_hook(self):
        self.temperature_controller.disable()
        return super(OsTechDiodeManager, self)._disable_hook()

    def get_additional_controls(self):
        gs = [VGroup(UCustom('temperature_controller',
                             editor=InstanceEditor(view='control_view')),
                     label='Watlow'),
              VGroup(UCustom('pyrometer', style='custom'),
                     label='Pyrometer'),
              VGroup(UCustom('fiber_light'), label='FiberLight')]
        return gs

    def _fiber_light_default(self):
        return FiberLight(name='fiber_light',
                          configuration_dir_name=self.configuration_dir_name)
# ============= EOF =============================================
