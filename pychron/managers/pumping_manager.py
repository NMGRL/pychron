##===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
##===============================================================================
#
#
#
##=============enthought library imports=======================
# from traits.api import HasTraits, Instance, Str, List
# from traitsui.api import View, Item, Group, VGroup
#
##=============standard library imports ========================
#
#
##=============local library imports  ==========================
# from manager import Manager
# from pychron.led.led import LED
# from pychron.led.led_editor import LEDEditor
# from pyface.timer.do_later import do_later
# from pyface.timer.api import Timer
# from pychron.hardware.gauges.granville_phillips.micro_ion_controller import MicroIonController
#
# class PumpingSystem(HasTraits):
#    name = Str
#    relay1 = Instance(LED, ())
#    relay2 = Instance(LED, ())
#    relay3 = Instance(LED, ())
#    relay4 = Instance(LED, ())
#
#    prev_relay = None
#    controller = Instance(MicroIonController)
#
#    def _led_item_factory(self, name):
#        return Item(name, editor=LEDEditor(),
#                    #show_label=False,
#                    style='custom')
#
#    def update(self):
#        statefunc = lambda st: 2 if int(st) == 1 else 0
#
#        c = self.controller.get_process_control_status()
#
#        self.relay1.state = statefunc(c[2])
#        self.relay2.state = statefunc(c[3])
#        self.relay3.state = statefunc(c[4])
#        self.relay4.state = statefunc(c[5])
#
#    def traits_view(self):
#
#        cg1 = VGroup(
#                   self._led_item_factory('relay1'),
#                   self._led_item_factory('relay2'),
#                   show_border=True
#                  )
#        cg2 = VGroup(
#                  self._led_item_factory('relay3'),
#                  self._led_item_factory('relay4'),
#                  show_border=True
#                  )
#
#        v = View(
#               VGroup(cg1, cg2)
#               )
#        return v
#
#    def _relay1_default(self):
#        return LED()
#    def _relay2_default(self):
#        return LED()
#    def _relay3_default(self):
#        return LED()
#    def _relay4_default(self):
#        return LED()
#
# class PumpingManager(Manager):
#    systems = List
#    def set_systems(self, systems):
#        for s in systems:
#            ss = self._pumping_system_factory(*s)
#
#            self.add_trait(s[0], ss)
#            self.systems.append((s[0], ss))
#
#    def _pumping_system_factory(self, name, controller):
#        return PumpingSystem(name=name,
#                             controller=controller
#                             )
#
#    def traits_view(self):
#
#        vg = VGroup()
#        for ps in self.systems:
#            vg.content.append(Group(Item(ps[0], style='custom', show_label=False), show_border=True,
#                                   label=ps[0]
#                                   ))
#
#        v = View(vg, resizable=True)
#        return v
#
#    def start_scan(self):
#
#        self.timer = Timer(1000, self.process_control_update)
#
#    def process_control_update(self):
#        for _s, ss in self.systems:
#            ss.update()
#
#
#
# if __name__ == '__main__':
#
#    pm = PumpingManager()
#    pm.set_systems([('Roughing', MicroIonController()),
#                     ('Analytical', MicroIonController())
#                     ])
#
#    do_later(pm.start_scan)
#    pm.configure_traits()
#
##============= EOF ====================================
# #        if self.prev_relay is None:
# #            self.prev_relay=self.relay1
# #        else:
# #            m=cnt%4
# #            if m==0:
# #                self.relay1.state=0
# #                self.prev_relay=self.relay2
# #            elif m==1:
# #                self.relay2.state=0
# #                self.prev_relay=self.relay3
# #
# #            elif m==2:
# #                self.relay3.state=0
# #                self.prev_relay=self.relay4
# #            else:
# #                self.relay4.state=0
# #                self.prev_relay=self.relay1
# #
# #            self.prev_relay.state=2
# #
