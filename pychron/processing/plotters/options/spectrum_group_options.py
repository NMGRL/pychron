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
from traits.api import HasTraits, Str, Int, Bool, Button, Any, Float, Property, on_trait_change, Color, Range, List
from traitsui.api import View, UItem, Item, HGroup, VGroup, ListEditor, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


class SpectrumGroupOptions(HasTraits):
    color = Color
    alpha = Range(0, 100, 70)
    group_id = Int
    use_fill = Bool(True)
    line_color = Color
    bind_colors = Bool(True)
    line_width = Int(1)

    calculate_fixed_plateau = Bool(False)
    calculate_fixed_plateau_start = Str
    calculate_fixed_plateau_end = Str
    edit_button = Button

    def _color_changed(self):
        if self.bind_colors:
            self.line_color = self.color

    def _line_color_changed(self):
        if self.bind_colors:
            self.color = self.line_color

    def _bind_colors_changed(self, new):
        if new:
            self.line_color = self.color

    def traits_view(self):
        grps = self._get_groups()

        g = VGroup(Item('bind_colors'), *grps)

        g.show_border = True
        g.label = 'Group {}'.format(self.group_id + 1)
        v = View(g)
        return v

    def _get_groups(self):
        envelope_grp = VGroup(HGroup(UItem('use_fill'),
                                     Item('color')),
                              Item('alpha', label='Opacity'),
                              show_border=True,
                              label='Error Envelope')

        line_grp = VGroup(UItem('line_color'),
                          Item('line_width',
                               label='Width'),
                          show_border=True,
                          label='Line')

        plat_grp = HGroup(Item('calculate_fixed_plateau',
                               label='Fixed',
                               tooltip='Calculate a plateau over provided steps'),
                          Item('calculate_fixed_plateau_start', label='Start', enabled_when='calculate_fixed_plateau'),
                          Item('calculate_fixed_plateau_end', label='End', enabled_when='calculate_fixed_plateau'),
                          show_border=True, label='Calculate Plateau')

        return envelope_grp, line_grp, plat_grp

    def simple_view(self):
        grps = self._get_groups()
        g = VGroup(HGroup(Item('bind_colors'),
                          icon_button_editor('edit_button', 'cog')),
                   *grps)
        v = View(g)
        return v


class SpectrumGroupEditor(HasTraits):
    error_envelopes = List

    def traits_view(self):
        v = View(UItem('error_envelopes',
                       style='custom',
                       editor=ListEditor(mutable=False,
                                         style='custom',
                                         editor=InstanceEditor())),
                 buttons=['OK', 'Cancel', 'Revert'],
                 kind='livemodal', resizable=True,
                 height=700,
                 title='Error Envelope Colors')
        return v


# ============= EOF =============================================



