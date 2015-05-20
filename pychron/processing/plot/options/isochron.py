# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool, Float, Property, String, Enum, Color
from traitsui.api import VGroup, HGroup, Item, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.plot.options.age import AgeOptions
from pychron.processing.plot.options.base import dumpable
from pychron.processing.plot.options.option import InverseIsochronPlotOptions
from pychron.pychron_constants import FIT_ERROR_TYPES


class InverseIsochronOptions(AgeOptions):
    label = 'Inv. Isochron'

    plot_option_name = 'Inv. Isochron'
    plot_option_klass = InverseIsochronPlotOptions

    error_calc_method = dumpable(Enum, *FIT_ERROR_TYPES)
    fill_ellipses = dumpable(Bool, False)
    show_nominal_intercept = dumpable(Bool, False)
    nominal_intercept_label = dumpable(String, 'Atm', enter_set=True, auto_set=False)
    nominal_intercept_value = dumpable(Property, Float, depends_on='_nominal_intercept_value')
    _nominal_intercept_value = dumpable(Float, 295.5, enter_set=True, auto_set=False)
    invert_nominal_intercept = dumpable(Bool, True)
    inset_marker_size = dumpable(Float, 1.0)
    inset_marker_color = dumpable(Color, 'black')

    def _load_factory_defaults(self, yd):
        self._set_defaults(yd, 'nominal_intercept', ('nominal_intercept_label',
                                                     'nominal_intercept_value',
                                                     'show_nominal_intercept',
                                                     'invert_nominal_intercept'))
        self._set_defaults(yd, 'inset', ('inset_marker_size', 'inset_marker_color'))

    # def _get_dump_attrs(self):
    #     attrs = super(AgeOptions, self)._get_dump_attrs()
    #     attrs += ['fill_ellipses',
    #               'show_nominal_intercept',
    #               'nominal_intercept_label',
    #               '_nominal_intercept_value',
    #               'invert_nominal_intercept',
    #               'display_inset', 'inset_width', 'inset_height', 'inset_location',
    #               'inset_marker_size']
    #     return attrs

    def _get_groups(self):
        g = Group(Item('error_calc_method',
                       width=-150,
                       label='Error Calculation Method'),
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

        # egrp=Group(
        # label='Display')
        label_grp = VGroup(self._get_x_axis_group(),
                           self._get_y_axis_group(),
                           # self._get_indicator_font_group(),
                           self._get_label_font_group(),
                           label='Fonts')

        return (VGroup(self._get_title_group(),
                       # egrp,
                       g, g2, label='Options'), label_grp)

    def _set_nominal_intercept_value(self, v):
        self._nominal_intercept_value = v

    def _get_nominal_intercept_value(self):
        v = self._nominal_intercept_value
        if self.invert_nominal_intercept:
            v **= -1
        return v

# ============= EOF =============================================
