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



#=============enthought library imports=======================
from traits.api import List, HasTraits, Str, Float
from traitsui.api import View, Item, ListEditor, InstanceEditor, HGroup

from pychron.managers.manager import Manager
import time
#============= standard library imports ========================
#============= local library imports  ==========================

# class Gauge(HasTraits):
#    name = Str
#    pressure = Float
#    def traits_view(self):
#        v = View(HGroup(Item('name', show_label=False, style='readonly'),
#                         Item('pressure', format_str='%0.2e', show_label=False, style='readonly')))
#        return v

class GaugeManager(Manager):
#    gauges = List
#    def finish_loading(self, *args, **kw):
#        for di in self.devices:
#            if hasattr(di, 'gauges'):
#                self.gauges.extend(di.gauges)

    def finish_loading(self, *args, **kw):
        width = int(250 / float(len(self.devices)))
        for k in self.devices:
            if hasattr(k, 'gauges'):
                for gi in k.gauges:
                    gi.width = width
#        self.load_gauges()
#        print 'load gm', args, kw
#
#        for k, v in self.traits().items():
#            if 'gauge_controller' in k:
#                print v
    def get_pressure(self, controller, name):
        dev = next((di for di in self.devices if di.name == controller), None)
        if dev is not None:
            gauge = dev.get_gauge(name)
            if gauge is not None:
                return gauge.pressure

    def stop_scans(self):
        for k in self.devices:
            if k.is_scanable:
                k.stop_scan()

    def start_scans(self):
        self.info('starting gauge scans')
        # stop scans first
        self.stop_scans()

        for k in self.devices:
            if k.is_scanable:
                k.start_scan()
                # stagger starts to reduce collisions
                time.sleep(0.25)
#            if 'gauge_controller' in k:
#                print v
#                v.start_scan()
# #
    def traits_view(self):

        v = View(Item('devices', style='custom',
                      show_label=False,
                      editor=ListEditor(mutable=False,
                                        columns=len(self.devices),
                                        style='custom',
                                        editor=InstanceEditor(view='gauge_view'))),
                 height=-100
                 )
        return v
#    controllers = List(GaugeControllers)
if __name__ == '__main__':
    g = GaugeManager()
    g.configure_traits()
#============= EOF =====================================
