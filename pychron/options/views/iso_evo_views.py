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
from traits.api import Bool, Enum, on_trait_change, Float, Int, Range
from traitsui.api import EnumEditor, Item, HGroup, UItem, View, VGroup, Tabbed

from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.options.options import AppearanceSubOptions, SubOptions, MainOptions, object_column, checkbox_column
from pychron.pychron_constants import FIT_TYPES, FIT_ERROR_TYPES


class IsoEvoSubOptions(SubOptions):
    pass


class IsoEvoAppearanceOptions(AppearanceSubOptions):
    pass


class IsoEvoMainOptions(MainOptions):
    plot_enabled = Bool
    save_enabled = Bool
    fit = Enum(FIT_TYPES)
    error_type = Enum(FIT_ERROR_TYPES)
    filter_outliers = Bool

    goodness_threshold = Float  # in percent
    slope_goodness = Float
    slope_goodness_intensity = Float
    outlier_goodness = Int
    curvature_goodness = Float
    curvature_goodness_at = Float
    rsquared_goodness = Range(0.0, 1.0, 0.95)
    signal_to_blank_goodness = Float
    global_goodness_visible = Bool

    def _get_edit_view(self):
        main = VGroup(HGroup(Item('name', editor=EnumEditor(name='names')),
                             Item('fit', editor=EnumEditor(values=FIT_TYPES)),
                             UItem('error_type', editor=EnumEditor(values=FIT_ERROR_TYPES))),
                      label='Fits')

        goodness = VGroup(Item('goodness_threshold', label='Intercept',
                               tooltip='If % error is greater than "Goodness Threshold" '
                                       'mark regression as "Bad"'),
                          HGroup(Item('slope_goodness', label='Slope',
                                      tooltip='If slope of regression is positive and the isotope '
                                              'intensity is greater than "Slope Goodness Intensity" '
                                              'then mark regression as "Bad"'),
                                 Item('slope_goodness_intensity', label='Intensity')),
                          Item('outlier_goodness', label='Outlier',
                               tooltip='If more than "Outlier Goodness" points are identified as outliers'
                                       'then mark regression as "Bad"'),
                          HGroup(Item('curvature_goodness', label='Curvature'),
                                 Item('curvature_goodness_at', label='Curvature At')),
                          HGroup(Item('rsquared_goodness', label='R-Squared Adj')),
                          HGroup(Item('signal_to_blank_goodness',
                                      tooltip='If Blank/Signal*100 greater than threshold mark regression as "Bad"')),
                          label='Goodness')

        auto = VGroup(VGroup(Item('n_threshold', label='Threshold'),
                             Item('n_true', label='N>=', tooltip='Fit when ncounts > Threshold'),
                             Item('n_false', label='N<', tooltip='Fit when ncounts < Threshold'),
                             label='N'),
                      label='Auto', enabled_when='fit=="Auto"')
        v = View(Tabbed(main, goodness, auto))
        return v

    def _get_global_group(self):
        g = BorderHGroup(Item('controller.save_enabled', label='Enabled'),
                         Item('controller.fit'),
                         UItem('controller.error_type', width=-75),
                         Item('controller.filter_outliers', label='Filter Outliers'),
                         Item('show_sniff'))

        gg = BorderVGroup(Item('controller.goodness_threshold', label='Intercept Goodness',
                               tooltip='If % error is greater than "Goodness Threshold" '
                                       'mark regression as "Bad"'),
                          HGroup(Item('controller.slope_goodness', label='Slope Goodness',
                                      tooltip='If slope of regression is positive and the isotope '
                                              'intensity is greater than "Slope Goodness Intensity" '
                                              'then mark regression as "Bad"'),
                                 Item('controller.slope_goodness_intensity', label='Intensity')),
                          Item('controller.outlier_goodness', label='Outlier Goodness',
                               tooltip='If more than "Outlier Goodness" points are identified as outliers'
                                       'then mark regression as "Bad"'),
                          HGroup(Item('controller.curvature_goodness'),
                                 Item('controller.curvature_goodness_at')),
                          HGroup(Item('controller.rsquared_goodness',
                                      tooltip='If R-squared is less than threshold mark regression as "Bad"')),
                          HGroup(Item('controller.signal_to_blank_goodness',
                                 tooltip='If Blank/Signal*100 greater than threshold mark regression as "Bad"')))

        agrp = self._get_analysis_group()
        return VGroup(agrp,
                      Item('controller.global_goodness_visible', label='Global Edit Visible'),
                      BorderVGroup(g, gg, label='Global', visible_when='controller.global_goodness_visible'))

    @on_trait_change('plot_enabled, save_enabled, fit, error_type, filter_outliers,'
                     'goodness_threshold, slope_goodness, slope_goodness_intensity,'
                     'outlier_goodness, curvature_goodness, curvature_goodness_at,'
                     'rsquared_goodness, signal_to_blank_goodness')
    def _handle_global(self, name, new):
        self._toggle_attr(name, new)

    def _toggle_attr(self, attr, new):
        items = self.model.selected
        if not items:
            items = self.model.aux_plots

        for a in items:
            setattr(a, attr, new)

    def _get_columns(self):
        cols = [object_column(name='name', editable=False),
                # checkbox_column(name='plot_enabled', label='Plot'),
                checkbox_column(name='save_enabled', label='Enabled'),
                object_column(name='fit',
                              editor=EnumEditor(name='fit_types'),
                              width=75),
                object_column(name='error_type',
                              editor=EnumEditor(name='error_types'),
                              width=75, label='Error'),
                checkbox_column(name='filter_outliers', label='Out.'),
                object_column(name='filter_outlier_iterations', label='Iter.'),
                object_column(name='filter_outlier_std_devs', label='NSigma'),
                checkbox_column(name='use_standard_deviation_filtering', label='Use SD'),
                object_column(name='truncate', label='Trunc.'),
                checkbox_column(name='include_baseline_error', label='Inc. BsErr')]
        return cols


VIEWS = {'main': IsoEvoMainOptions,
         'isoevo': IsoEvoSubOptions,
         'appearance': IsoEvoAppearanceOptions}
# ============= EOF =============================================
