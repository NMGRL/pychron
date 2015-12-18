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
from pychron.mv.machine_vision_manager import MachineVisionManager


class AutoCenterManager(MachineVisionManager):
    canvas = Any
    crop_size = Float(4)
    configure_button = Button('configure')
    use_autocenter = Bool
    target_radius = Float(1.5)

    def calculate_new_center(self, cx, cy, dim=1.5):
        frame = self.new_image_frame()
        im = self.new_image(frame)
        self.view_image(im)

        loc = self.get_locator()
        cw = ch = self.crop_size
        frame = loc.crop(im.source_frame, cw, ch)
        dx, dy = loc.find(im, frame, dim=dim * self.pxpermm)
        if dx and dy:
            pdx, pdy = round(dx), round(dy)
            mdx = pdx / self.pxpermm
            mdy = pdy / self.pxpermm
            self.info('calculated deviation px={:n},{:n}, mm={:0.3f},{:0.3f}'.format(pdx, pdy,
                                                                                     mdx, mdy))

            return cx + mdx, cy + mdy

    # private
    def _get_locator(self):
        raise NotImplementedError

    # handlers
    def _configure_button_fired(self):
        w = h = self.crop_size * self.pxpermm
        cx, cy = self.canvas.get_center_rect_position(w, h)

        self.canvas.add_markup_rect(cx, cy, w, h, identifier='croprect')

        cx, cy = self.canvas.get_screen_center()
        r = self.target_radius * self.pxpermm
        print cx, cy, r
        self.canvas.add_markup_circle(cx, cy, r, identifier='target')

        self.edit_traits(view='configure_view', kind='livemodal')

        self.canvas.remove_item('croprect')
        self.canvas.remove_item('target')

    def _crop_size_changed(self):
        self.canvas.remove_item('croprect')

        w = h = self.crop_size * self.pxpermm
        cx, cy = self.canvas.get_center_rect_position(w, h)

        self.canvas.add_markup_rect(cx, cy, w, h, identifier='croprect')

    def _target_radius_changed(self):
        self.canvas.remove_item('target')
        r = self.target_radius * self.pxpermm
        cx, cy = self.canvas.get_screen_center()
        self.canvas.add_markup_circle(cx, cy, r, identifier='target')

    # views
    def configure_view(self):
        v = View(Item('crop_size'),
                 Item('target_radius', editor=RangeEditor(low=0., high=5.)),
                 buttons=['OK', 'Cancel'])
        return v

    def traits_view(self):
        v = View(HGroup(
                      Item('use_autocenter', label='Enabled'),
                      Item('configure_button', show_label=False),
                      show_border=True,
                      label='Autocenter'))
        return v


class CO2AutocenterManager(AutoCenterManager):
    # private
    def _get_locator(self):
        from pychron.mv.co2_locator import CO2Locator
        return CO2Locator(pxpermm=self.pxpermm)
# ============= EOF =============================================
