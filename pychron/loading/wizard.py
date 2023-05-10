# ===============================================================================
# Copyright 2023 Jake Ross
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
from threading import Thread

from pychron.loggable import Loggable
from traits.api import Button, Bool, observe
from traitsui.api import View, Item, UItem, HGroup, VGroup, spring, EnumEditor, spring


class DoNothing(Button):
    def __init__(self, *args, **kw):
        super().__init__(do_nothing=True, *args, **kw)


class LoadingWizard(Loggable):
    dn_load_laser_tray_into_holder_button = DoNothing("Load Laser Tray into Holder")
    dn_load_laser_tray_into_holder_state = Bool(False)

    dn_place_square_plate_button = DoNothing("Place Square Plate")
    dn_place_square_plate_state = Bool(False)

    identify_and_calibrate_button = Button("Identify and Calibrate")
    identify_and_calibrate_state = Bool(False)

    check_empty_tray_button = Button("Check Empty Tray")
    check_empty_tray_state = Bool(False)

    load_samples_button = Button("Load Samples")
    load_samples_state = Bool(False)

    check_loaded_tray_button = Button("Check Loaded Tray")
    check_loaded_tray_state = Bool(False)

    active_thread = None

    @observe('+do_nothing')
    def _handle_do_nothing(self,event):
        print(event)
        name = event.name
        name = name.replace('_button', '_state')
        cv = getattr(self, name)
        setattr(self, name, not cv)

    def _identify_and_calibrate_button_fired(self):
        # if self.active_thread:
        #     self.manager.cancel_identify_and_calibrate()
        #     return
        # self.manager.alive = True
        # self.active_thread = Thread(target=self.manager.identify_and_calibrate)
        # self.active_thread.start()
        tray_name = self.manager.identify()
        if tray_name:
            if self.confirmation_dialog(f'Tray Identified as {tray_name}. Is this correct?'):
                self.manager.tray = ''
                self.manager.tray = tray_name
                self.identify_and_calibrate_state = not self.identify_and_calibrate_state
            else:
                return

            self.debug('calibrate tray')
            self.manager.stage_manager.tray_calibration_manager.style = 'Auto'
            self.manager.stage_manager.tray_calibration_manager.calibrate = True

    def _check_empty_tray_button_fired(self):
        self.check_empty_tray_state = not self.check_empty_tray_state

    def _load_samples_button_fired(self):
        self.load_samples_state = not self.load_samples_state

    def _check_loaded_tray_button_fired(self):
        self.check_loaded_tray_state = not self.check_loaded_tray_state

    # def traits_view(self):
    #     v = View(VGroup(HGroup(UItem('dn_load_laser_tray_into_holder_button'),
    #                            spring,
    #                            UItem('dn_load_laser_tray_into_holder_state')),
    #                     HGroup(UItem('dn_place_square_plate_button'),
    #                            spring,
    #                            UItem('dn_place_square_plate_state')),
    #                     HGroup(UItem('identify_and_calibrate_button'),
    #                            spring,
    #                            UItem('identify_and_calibrate_state')),
    #                     HGroup(UItem('check_empty_tray_button'),
    #                            spring,
    #                            UItem('check_empty_tray_state')),
    #                     HGroup(UItem('load_samples_button'),
    #                            spring,
    #                            UItem('load_samples_state')),
    #                     HGroup(UItem('check_loaded_tray_button'),
    #                            spring,
    #                            UItem('check_loaded_tray_state')),
    #
    #                     ),
    #
    #              title='Loading Wizard',
    #              resizable=True,
    #              width=500,
    #              height=500,
    #              buttons=['OK', 'Cancel'],
    #              kind='livemodal'
    #              )
    #     return v


if __name__ == '__main__':
    lw = LoadingWizard()
    lw.configure_traits()
# ============= EOF =============================================
