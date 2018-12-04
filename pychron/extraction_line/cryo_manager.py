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
from traitsui.api import View, Item, InstanceEditor, ListEditor

from pychron.core.helpers.strtools import csv_to_floats
from pychron.managers.manager import Manager
from pychron.paths import paths


class CryoManager(Manager):
    species = Enum('He', 'Ar/Ar', 'Ne')

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

    def read_input(self, iput, idx=0):
        dev = self.devices[idx]
        return dev.read_input(iput)

    def set_setpoint(self, v1, v2=None, idx=0):
        """
        v is either a float or a str
        if float interpret as degrees K
        if str lookup species in cryotemps.yaml
        :param v:
        :return:
        """
        try:
            v1 = float(v1)
        except ValueError:
            v1, v2 = self._lookup_species_temp(v1)

        if v1 is not None:
            self.devices[idx].set_setpoints(v1, v2)

        self.debug('set_setpoint returning "{}","{}"'.format(v1, v2))
        return v1, v2

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
            s = 'Ar' if self.species == 'Ar/Ar' else self.species
            v = '{}_{}'.format(s, v)

        p = os.path.join(paths.device_dir, 'cryotemps.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                yd = yaml.load(fp)
                return csv_to_floats(yd[v])
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
            v = View()
        return v

    def _get_simulation(self):
        return any([dev.simulation for dev in self.devices])
# ============= EOF =============================================
