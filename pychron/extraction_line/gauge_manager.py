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
from traits.api import Int, Bool
from traitsui.api import View, Item, ListEditor, InstanceEditor
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.managers.manager import Manager


class GaugeManager(Manager):
    use_update = Bool
    update_period = Int

    def finish_loading(self, *args, **kw):
        width = int(250 / float(len(self.devices)))
        for k in self.devices:
            if hasattr(k, 'gauges'):
                for gi in k.gauges:
                    gi.width = width
                    # if gi.name in ('CG1', 'CG2'):
                    #     gi.pressure = random.randint(1, 50) * 1e-2
                    # else:
                    #     gi.pressure = random.randint(1, 50) * 1e-8

    def get_pressure(self, controller, name):
        dev = next((di for di in self.devices if di.name == controller), None)
        if dev is None:
            self.warning('Failed getting pressure for {} {}. '
                         'Not a valid controller'.format(controller, name))
        else:
            return dev.get_pressure(name)

    def test_connection(self):
        print self.devices

        for di in self.devices:
            if not di.test_connection():
                self.debug('Failed connection to "{}" (display_name={})'.format(di.name, di.display_name))
                return
            else:
                self.debug('Get pressures name={}, display_name={}, {}'.format(di.name,
                                                                               di.display_name,
                                                                               di.get_pressures(verbose=True)))
        else:
            return True

    def stop_scans(self):
        for k in self.devices:
            if k.is_scanable:
                k.stop_scan()

    def start_scans(self):

        self.info('starting gauge scans')
        # stop scans first
        self.stop_scans()

        # sp = self.scan_period*1000
        sp = None
        if self.use_update:
            sp = self.update_period

        sp = sp or None
        for k in self.devices:
            if k.is_scanable:

                k.start_scan(sp)
                # stagger starts to reduce collisions
                time.sleep(0.25)

    def traits_view(self):

        v = View(Item('devices', style='custom',
                      show_label=False,
                      editor=ListEditor(mutable=False,
                                        columns=len(self.devices),
                                        style='custom',
                                        editor=InstanceEditor(view='gauge_view'))),
                 height=-100)
        return v

    def _get_simulation(self):
        return any([dev.simulation for dev in self.devices])

if __name__ == '__main__':
    g = GaugeManager()
    g.bootstrap()
    # g.configure_traits()
# ============= EOF =====================================
