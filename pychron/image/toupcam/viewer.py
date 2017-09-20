# # ===============================================================================
# # Copyright 2015 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
# from traits.api import HasTraits, Instance, Button, Event, Range, on_trait_change
# from traitsui.api import View, UItem, Item, HGroup, VGroup, spring
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# from pychron.core.helpers.ctx_managers import no_update
# from pychron.core.helpers.filetools import unique_path2
# from pychron.core.ui.qt.camera_editor import CameraEditor
#
# from pychron.image.toupcam.camera import ToupCamCamera
# from pychron.paths import paths
#
#
# class D(HasTraits):
#     camera = Instance(ToupCamCamera, ())
#     save_button = Button
#     save_event = Event
#     awb_button = Button
#     contrast_default_button = Button('Defaults')
#     hue_default_button = Button('Defaults')
#
#     temperature = Range(2000, 15000, mode='slider')
#     tint = Range(200, 2500, mode='slider')
#     hue = Range(-180, 180, mode='slider')
#     saturation = Range(0, 255, mode='slider')
#     brightness = Range(-64, 64, mode='slider')
#     contrast = Range(-100, 100, mode='slider')
#     gamma = Range(0, 180, mode='slider')
#
#     _no_update = False
#
#     def activate(self):
#         self.camera.open()
#         self._update_color()
#
#     # handlers
#     def _awb_button_fired(self):
#         self.camera.do_awb(self._update_temptint)
#
#     def _save_button_fired(self):
#         # p = '/Users/ross/Desktop/output_uint8.jpg'
#         p, _ = unique_path2(paths.sample_image_dir, 'nosample', extension='.tiff')
#         self.camera.save(p)
#         # self.save_event = p
#
#
#     def _hue_default_button_fired(self):
#         self.trait_set(hue=0, saturation=128, brightness=0)
#
#     def _contrast_default_button_fired(self):
#         self.trait_set(contrast=0, gamma=100)
#
#     @on_trait_change('hue,saturation,brightness,contrast,gamma')
#     def _handle_color_change(self, name, new):
#         if not self._no_update:
#             getattr(self.camera, 'set_{}'.format(name))(new)
#
#     def _temperature_changed(self):
#         self._set_temp_tint()
#
#     def _tint_changed(self):
#         self._set_temp_tint()
#
#     # private
#     def _update_temptint(self, args=None):
#         if args is None:
#             args = self.camera.get_temperature_tint()
#
#         if args:
#             with no_update(self):
#                 self.trait_set(temperature=int(args[0]), tint=int(args[1]))
#
#     def _set_temp_tint(self):
#         if not self._no_update:
#             self.camera.set_temperature_tint(self.temperature, self.tint)
#
#     def _update_color(self):
#         self._update_temptint()
#         with no_update(self):
#             d = {k: getattr(self.camera, 'get_{}'.format(k))() for k in
#                  ('hue', 'saturation', 'brightness', 'contrast', 'gamma')}
#             self.trait_set(**d)
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
#
#         v = View(HGroup(ctrl_grp,
#                         UItem('camera', editor=CameraEditor())),
#                  width=896 + 350, height=680,
#                  resizable=True)
#         return v
#
#
# if __name__ == '__main__':
#     paths.build('_dev')
#     d = D()
#     d.activate()
#
#     d.configure_traits()
#     d.camera.close()
#
# # ============= EOF =============================================
#
#
#
