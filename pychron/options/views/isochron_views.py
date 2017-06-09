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
from traitsui.api import View, Item, HGroup, VGroup, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import SubOptions, AppearanceSubOptions


class IsochronMainOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class IsochronAppearance(AppearanceSubOptions):
    pass


class InverseIsochronMainOptions(SubOptions):
    def traits_view(self):
        g = Group(Item('error_calc_method',
                       width=-150,
                       label='Error Calculation Method'),
                  show_border=True,
                  label='Calculations')

        g2 = Group(HGroup(Item('show_info', label='Show'),
                          label='Info'),
                   HGroup(Item('fill_ellipses', ),
                          Item('label_box'),
                          show_border=True, label='Labels'),
                   VGroup(Item('show_nominal_intercept'),
                          HGroup(Item('nominal_intercept_label', label='Label', enabled_when='show_nominal_intercept'),
                                 Item('_nominal_intercept_value', label='Value', enabled_when='show_nominal_intercept'),
                                 Item('invert_nominal_intercept', label='Invert')),
                          show_border=True,
                          label='Nominal Intercept'),
                   VGroup(Item('display_inset'),
                          Item('inset_location'),
                          HGroup(Item('inset_marker_size', label='Marker Size'),
                                 Item('inset_marker_color', label='Color')),
                          HGroup(Item('inset_width', label='Width'),
                                 Item('inset_height', label='Height')),
                          show_border=True,
                          label='Inset'),
                   show_border=True,
                   label='Display')
        return self._make_view(VGroup(g, g2))


class InverseIsochronAppearance(AppearanceSubOptions):
    pass


# ===============================================================
# ===============================================================

ISOCHRON_VIEWS = {'main': IsochronMainOptions, 'appearance': IsochronAppearance}
INVERSE_ISOCHRON_VIEWS = {'main': InverseIsochronMainOptions, 'appearance': InverseIsochronAppearance}

# ============= EOF =============================================
