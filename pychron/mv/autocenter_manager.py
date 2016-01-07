# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Float, Button, Bool, Any
from traitsui.api import View, Item, HGroup, RangeEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.mv.machine_vision_manager import MachineVisionManager, view_image


class AutoCenterManager(MachineVisionManager):
    canvas = Any

    use_crop_size = Bool(False)
    use_target_radius = Bool(False)

    crop_size = Float(4)
    target_radius = Float(1.0)

    configure_button = Button('configure')
    use_autocenter = Bool
    use_hough_circle = Bool(True)
    
    def calculate_new_center(self, cx, cy, offx, offy, dim=1.0,
                             alpha_enabled=True,
                             auto_close_image=True):
        frame = self.new_image_frame()

        loc = self._get_locator()

        if self.use_target_radius:
            dim = self.target_radius

        if self.use_crop_size:
            cropdim = self.crop_size
        else:
            cropdim = dim*2.5

        frame = loc.crop(frame, cropdim, cropdim, offx, offy)
        im = self.new_image(frame, alpha_enabled=alpha_enabled)
        view_image(im, auto_close=auto_close_image)

        if self.use_hough_circle:
            dx, dy = loc.find_circle(im, frame, dim=dim * self.pxpermm)
        else:
            dx, dy = loc.find(im, frame, dim=dim * self.pxpermm)

        frm = loc.preprocessed_frame
        im.overlay(frm, 0.5)
        if dx is None and dy is None:
            return
        else:
            # pdx, pdy = round(dx), round(dy)
            mdx = dx / self.pxpermm
            mdy = dy / self.pxpermm
            self.info('calculated deviation px={:n},{:n}, '
                      'mm={:0.3f},{:0.3f} ({})'.format(dx, dy, mdx, mdy,
                                                       self.pxpermm))
            return cx + mdx, cy + mdy

    # private
    def _get_locator(self):
        raise NotImplementedError

    # handlers
    def _configure_button_fired(self):
        w = h = self.crop_size * self.pxpermm
        canvas = self.canvas
        if canvas:
            cx, cy = canvas.get_center_rect_position(w, h)

            canvas.add_markup_rect(cx, cy, w, h, identifier='croprect')

            cx, cy = canvas.get_screen_center()
            r = self.target_radius * self.pxpermm
            canvas.add_markup_circle(cx, cy, r, identifier='target')

        self.edit_traits(view='configure_view', kind='livemodal')
        if canvas:
            canvas.remove_item('croprect')
            canvas.remove_item('target')

    def _crop_size_changed(self):
        canvas = self.canvas
        if canvas:
            canvas.remove_item('croprect')

            w = h = self.crop_size * self.pxpermm
            cx, cy = canvas.get_center_rect_position(w, h)

            canvas.add_markup_rect(cx, cy, w, h, identifier='croprect')

    def _target_radius_changed(self):
        canvas = self.canvas
        if canvas:
            canvas.remove_item('target')
            r = self.target_radius * self.pxpermm
            cx, cy = canvas.get_screen_center()
            canvas.add_markup_circle(cx, cy, r, identifier='target')

    # views
    def configure_view(self):
        v = View(Item('crop_size'),
                 Item('target_radius', editor=RangeEditor(low=0., high=5.)),
                 buttons=['OK', 'Cancel'])
        return v

    def traits_view(self):
        v = View(HGroup(Item('use_autocenter', label='Enabled'),
                        Item('configure_button', show_label=False),
                        show_border=True,
                        label='Autocenter'))
        return v


class CO2AutocenterManager(AutoCenterManager):
    # private
    def _get_locator(self):
        from pychron.mv.co2_locator import CO2Locator
        return CO2Locator(pxpermm=self.pxpermm)


class DiodeAutocenterManager(AutoCenterManager):
    # private
    def _get_locator(self):
        from pychron.mv.diode_locator import DiodeLocator
        return DiodeLocator(pxpermm=self.pxpermm)

# ============= EOF =============================================
