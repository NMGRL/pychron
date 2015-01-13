# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import HasTraits, Instance, Button, Event, Range
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import view_file
from pychron.core.ui.qt.camera_editor import CameraEditor

from pychron.image.toupcam.camera import ToupCamCamera


class D(HasTraits):
    camera = Instance(ToupCamCamera, ())
    save_button = Button
    save_event = Event
    awb_button = Button
    temperature = Range(2000, 15000, mode='slider')
    tint = Range(200, 2500, mode='slider')

    _no_update = False

    def activate(self):
        self.camera.open()
        self._update_temptint()

    def _awb_button_fired(self):
        self.camera.do_awb(self._update_temptint)

    def _save_button_fired(self):
        p = '/Users/ross/Desktop/output.png'
        # self.camera.save(p)
        self.save_event = p
        view_file(p)

    def _temperature_changed(self):
        self._set_temp_tint()

    def _tint_changed(self):
        self._set_temp_tint()

    def _update_temptint(self, args=None):
        if args is None:
            args = self.camera.get_temperature_tint()

        if args:
            with no_update(self):
                self.trait_set(temperature=int(args[0]), tint=int(args[1]))

    def _set_temp_tint(self):
        if not self._no_update:
            self.camera.set_temperature_tint(self.temperature, self.tint)

    def traits_view(self):
        ctrl_grp = VGroup(UItem('save_button'),
                          UItem('awb_button'),
                          Item('temperature', label='Temp.', width=300),
                          Item('tint'))

        v = View(HGroup(ctrl_grp,
                        UItem('camera', editor=CameraEditor(save_event='save_event'))),
                 width=896+350, height=680,
                 resizable=True)
        return v


if __name__ == '__main__':
    d = D()
    d.activate()

    d.configure_traits()
    d.camera.close()

# ============= EOF =============================================



