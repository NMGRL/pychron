# ===============================================================================
# Copyright 2018 ross
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
import os
import yaml
from traits.api import Enum
from traitsui.api import View, UItem, Item, InstanceEditor, ListEditor

import time
from pychron.managers.manager import Manager
from pychron.paths import paths


class CryoManager(Manager):
    species = Enum('He', 'Ar', 'Ne')

    def finish_loading(self, *args, **kw):
        pass

    # def get_pressure(self, controller, name):
    #     dev = next((di for di in self.devices if di.name == controller), None)
    #     if dev is None:
    #         self.warning('Failed getting pressure for {} {}. '
    #                      'Not a valid controller'.format(controller, name))
    #     else:
    #         return dev.get_pressure(name)

    def test_connection(self):
        for di in self.devices:
            if not di.test_connection():
                self.debug('Failed connection to "{}" '.format(di.name))
                return False
        else:
            return True

    # def stop_scans(self):
    #     for k in self.devices:
    #         if k.is_scanable:
    #             k.stop_scan()
    #
    # def start_scans(self):
    #
    #     self.info('starting gauge scans')
    #     # stop scans first
    #     self.stop_scans()
    #
    #     # sp = self.scan_period*1000
    #     sp = None
    #     if self.use_update:
    #         sp = self.update_period*1000
    #
    #     sp = sp or None
    #     for k in self.devices:
    #         if k.is_scanable:
    #             k.start_scan(sp)
    #             # stagger starts to reduce collisions
    #             time.sleep(0.25)
    def set_setpoint(self, v, output=1, idx=0):
        """
        v is either a float or a str
        if float interpret as degrees K
        if str lookup species in cryotemps.yaml
        :param v:
        :return:
        """
        try:
            v = float(v)
        except ValueError:
            v = self._lookup_species_temp(v)

        if v is not None:
            self.devices[idx].set_setpoint(v, output)

    def _lookup_species_temp(self, v):
        """
        valid v

        He_freeze
        freeze
        pump
        release


        :param v:
        :return:
        """

        if v in ('freeze', 'pump', 'release'):
            v = '{}_{}'.format(self.species, v)

        p = os.path.join(paths.device_dir, 'cryotemps.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                yd = yaml.load(fp)
                return yd[v]
        else:
            self.warning('File {} does not exist. Cryostat setpoint can not be set')

    def traits_view(self):
        if self.devices:
            v = View(Item('devices', style='custom',
                          show_label=False,
                          editor=ListEditor(mutable=False,
                                            columns=len(self.devices),
                                            style='custom',
                                            editor=InstanceEditor(view='control_view'))),
                     height=-100)
        else:
            v =View()
        return v

    def _get_simulation(self):
        return any([dev.simulation for dev in self.devices])
# ============= EOF =============================================
