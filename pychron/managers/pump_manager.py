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



from traits.api import Instance, Str, Event, Property, Bool, Int
from traitsui.api import View, Item, HGroup, ButtonEditor

from pychron.managers.manager import Manager
from pychron.hardware.core.core_device import CoreDevice


class PumpController(CoreDevice):
    name = Str

    valve_button = Event
    pump_button = Event

    valve_label = Property(depends_on='_valve_state')
    _valve_state = Bool

    pump_label = Property(depends_on='_pump_state')
    _pump_state = Bool


    valve_sol = Int
    valve_io = Int
    valve_ic = Int

    pump_relay = Int


    command_keys = dict(open=1, close=2, io=3, ic=4, on=1, off=2)

    def build_message(self, pin, key, terminator=';'):
        return '{},{}{}'.format(pin, self.command_keys[key], terminator)

    def load_additional_args(self, config):
        self.set_attribute(config, 'valve_sol', 'PinMapping', 'sol', cast='int')
        self.set_attribute(config, 'valve_io', 'PinMapping', 'io', cast='int')
        self.set_attribute(config, 'valve_ic', 'PinMapping', 'ic', cast='int')
        self.set_attribute(config, 'pump_relay', 'PinMapping', 'relay', cast='int')

    def _get_valve_label(self):
        return 'Open' if self._valve_state else 'Close'

    def _get_pump_label(self):
        return 'ON' if self._pump_state else 'OFF'

    def _valve_button_fired(self):
        cmd = 'close' if self._valve_state else 'open'
        cmd = self.build_message(self.valve_sol, cmd)
        self.ask(cmd)

        self._valve_state = not self._valve_state

    def _pump_button_fired(self):
        cmd = 'off' if self._pump_state else 'on'
        cmd = self.build_message(self.valve_sol, cmd)
        self.ask(cmd)

        self._pump_state = not self._pump_state

    def traits_view(self):
        return View(Item('name'),
                    Item('valve_button', label='Valve', editor=ButtonEditor(label_value='valve_label')),
                    Item('pump_button', label='Pump', editor=ButtonEditor(label_value='pump_label'))
                    )


class PumpManager(Manager):
    pumpcontroller1 = Instance(PumpController)
    pumpcontroller2 = Instance(PumpController)
    pumpcontroller3 = Instance(PumpController)
    pumpcontroller4 = Instance(PumpController)

    def traits_view(self):
        grp = HGroup()
        for controller in self.get_controller_names():
            grp.content.append(Item(controller, show_label=False, style='custom'))

        v = View(grp)
        return v

    def get_controller_names(self):
        return ['pumpcontroller{}'.format(i + 1) for i in range(4)]

    def get_controllers(self):
        return [getattr(self, name) for name in self.get_controller_names()]

    def load_controllers(self):
        for controller in self.get_controller_names():
            p = PumpController(name=controller,
                               configuration_dir_name='pumping')
            p.bootstrap()
            setattr(self, controller, p)


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup(name='pumpman')
    c = PumpManager()
    c.load_controllers()
    c.configure_traits()
