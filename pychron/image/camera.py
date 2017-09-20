# ===============================================================================
# Copyright 2014 Jake Ross
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
import os

from traits.api import HasTraits, provides, Button, Event, Range,Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traits.has_traits import on_trait_change
from traitsui.api import View, UItem, VGroup, VFold, HSplit, Item, HGroup, spring
from traitsui.menu import Action, ToolBar

from pychron.core.helpers.ctx_managers import no_update
from pychron.core.ui.qt.camera_editor import CameraEditor
from pychron.envisage.resources import icon
from pychron.image.i_camera import ICamera
from pychron.image.toupcam.camera import ToupCamCamera
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin


@provides(ICamera)
class Camera(HasTraits, PersistenceMixin):
    _device = Any
    configure = Button
    snapshot_event = Event
    temperature = Range(2000, 15000, mode='slider', dump=True)
    tint = Range(200, 2500, mode='slider', dump=True)
    hue = Range(-180, 180, mode='slider', dump=True)
    saturation = Range(0, 255, mode='slider')
    brightness = Range(-64, 64, mode='slider')
    contrast = Range(-100, 100, mode='slider')
    gamma = Range(0, 180, mode='slider')

    awb_button = Button('Auto')
    contrast_default_button = Button('Defaults')
    hue_default_button = Button('Defaults')

    _no_update = False

    @property
    def persistence_path(self):
        try:
            return os.path.join(paths.hidden_dir, 'camera_settings')
        except AttributeError:
            return os.path.join(os.path.expanduser('~'), 'Desktop', 'camera_settings')

    def activate(self):
        self.open()
        self.load()
        self._update_color()

    def save_jpeg(self, p):
        self._device.save_jpeg(p)

    # handlers
    def _awb_button_fired(self):
        if self._device:
            self._device.do_awb(self._update_temptint)

    def _hue_default_button_fired(self):
        self.trait_set(hue=0, saturation=128, brightness=0)

    def _contrast_default_button_fired(self):
        self.trait_set(contrast=0, gamma=100)

    @on_trait_change('hue,saturation,brightness,contrast,gamma')
    def _handle_color_change(self, name, new):
        if self._device is not None:
            if not self._no_update:
                getattr(self._device, 'set_{}'.format(name))(new)

    def _temperature_changed(self):
        self._set_temp_tint()

    def _tint_changed(self):
        self._set_temp_tint()

    # private
    def _update_temptint(self, args=None):
        if args is None:
            args = self._device.get_temperature_tint()

        if args:
            with no_update(self):
                self.trait_set(temperature=int(args[0]), tint=int(args[1]))

    def _set_temp_tint(self):
        if not self._no_update:
            self._device.set_temperature_tint(self.temperature, self.tint)

    def _update_color(self):
        self._update_temptint()
        with no_update(self):
            d = {k: getattr(self._device, 'get_{}'.format(k))() for k in
                 ('hue', 'saturation', 'brightness', 'contrast', 'gamma')}
            print 'dasfa', d
            try:
                self.trait_set(**d)
            except TypeError:
                pass

    #
    #     def traits_view(self):
    #         hue_grp = VGroup(HGroup(spring, UItem('hue_default_button')),
    #                          Item('hue'),
    #                          Item('saturation'),
    #                          Item('brightness'),
    #                          show_border=True,
    #                          label='Hue/Saturation/Brightness')
    #         c_gamma_grp = VGroup(HGroup(spring, UItem('contrast_default_button')),
    #                              Item('contrast'),
    #                              Item('gamma'),
    #                              show_border=True,
    #                              label='Contrast/Gamma')
    #
    #         ctrl_grp = VGroup(UItem('save_button'),
    #                           UItem('awb_button'),
    #                           Item('temperature', label='Temp.', width=300),
    #                           Item('tint'),
    #                           hue_grp, c_gamma_grp)

    # deff __getattr__(self, item):
    #     try:
    #         return getattr(self._device, item)
    #     except AttributeError:
    #         pass

    def open(self):
        self._device = ToupCamCamera()
        self._device.open()

    def close(self):
        self._device.close()

    def _configure_fired(self):
        pass

    def do_snapshot(self):
        self.snapshot_event = True

    def save_settings(self):
        pass

    def load_settings(self):
        pass

    def traits_view(self):
        hue_grp = VGroup(HGroup(spring, UItem('hue_default_button')),
                         Item('hue'),
                         Item('saturation'),
                         Item('brightness'),
                         show_border=True,
                         label='Hue/Saturation/Brightness')

        c_gamma_grp = VGroup(HGroup(spring, UItem('contrast_default_button')),
                             Item('contrast'),
                             Item('gamma'),
                             show_border=True,
                             label='Contrast/Gamma')

        # ctrl_grp = VGroup(UItem('save_button'),
        #                   UItem('awb_button'),
        #                   Item('temperature', label='Temp.', width=300),
        #                   Item('tint'),
        #                   hue_grp, c_gamma_grp)
        #
        # exposure_grp = VGroup(label='Exposure')
        white_balance_grp = VGroup(UItem('awb_button'),
                                   label='White Balance')
        # color_grp = VGroup(label='Color')

        ctrlgrp = VFold(hue_grp,
                        c_gamma_grp,
                        white_balance_grp)

        v = View(HSplit(ctrlgrp,
                        VGroup(UItem('_device',
                                     width=640, height=480,
                                     editor=CameraEditor()))),
                 toolbar=ToolBar(Action(action='do_snapshot',
                                        image=icon('camera'),
                                        ),
                                 # Action(action='save_settings',
                                 #        image=icon('cog'))
                                 ),
                 title='Camera')
        return v

        # _owners = None
        #
        # def close(self):
        #     pass
        #
        # def open(self, owner=None):
        #     self._device = get_capture_device()
        #     self._device.open(0)
        #
        #     if self._owners is None:
        #         self._owners = []
        #
        #     if owner is None:
        #         stack = inspect.stack()
        #
        #         # cstack = stack[0]
        #         rstack = stack[1]
        #
        #         owner = hash(rstack[3])
        #
        #     if owner not in self._owners:
        #         self._owners.append(owner)
        #
        # def retrieve_frame(self):
        #     """
        #         get a raw frame from the device
        #     :return:
        #     """
        #     if self._device:
        #         state, img = self._device.read()
        #         if state:
        #             return img
        #
        # def render_frame(self, src=None, size=None):
        #     """
        #         render the raw frame into the final version. i.e flip,rotate, swap channels etc
        #     :return:
        #     """
        #     if src is None:
        #         src = self.retrieve_frame()
        #
        #     img = self.post_process(src, size=size)
        #     return img
        #
        # def get_image_data(self, *args, **kw):
        #     img = self.render_frame(*args, **kw)
        #     return asarray(img)
        #
        # def post_process(self, img, size=None, swap=True):
        #     if img is not None:
        #         if size:
        #             img = resize(img, *size)
        #
        #         if swap:
        #             img = swap_rb(img)
        #     return img
        #
        # def save(self, path, src=None):
        #     if src is None:
        #         src = self.render_frame()
        #
        #     save_image(src, path)


if __name__ == '__main__':
    c = Camera()
    c.load()
    c.configure_traits()
    c.dump()
# ============= EOF =============================================
