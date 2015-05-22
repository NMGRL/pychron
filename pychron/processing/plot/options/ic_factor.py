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
from enable.markers import marker_names
from traits.api import List, Property, Str, Float
from traitsui.api import EnumEditor, View, Item, UItem, VGroup, HGroup, Label
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.fits.fit import Fit
from pychron.processing.plot.options.figure_plotter_options import object_column, checkbox_column
from pychron.processing.plot.options.fit import FitOptions
from pychron.processing.plot.options.option import AuxPlotOptions
from pychron.pychron_constants import FIT_TYPES_INTERPOLATE


class ICFactorAuxPlot(AuxPlotOptions, Fit):
    # names = List([, ])
    # numerators = List
    # denominators = List
    name = Property

    detectors = List
    numerator = Str
    denominator = Str
    analysis_type = Str
    analysis_types = List
    standard_ratio = Float
    standard_ratios = List((295.5,))

    def _analysis_types_default(self):
        from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING

        return ANALYSIS_MAPPING.values()

    def _get_name(self):
        return '{}/{}'.format(self.numerator, self.denominator)

    def _get_fit_types(self):
        return FIT_TYPES_INTERPOLATE


class ICFactorOptions(FitOptions):
    plot_option_klass = ICFactorAuxPlot

    def set_aux_plots(self, ps):
        pp = []
        for pd in ps:
            pp.append(self.plot_option_klass(**pd))

        n = 5 - len(pp)
        if n:
            pp.extend((self.plot_option_klass() for i in xrange(n)))

        self.aux_plots = pp

    def _get_edit_view(self):
        f = VGroup(HGroup(UItem('numerator', editor=EnumEditor(name='detectors')), Label('/'),
                          UItem('denominator', editor=EnumEditor(name='detectors'))),
                   Item('analysis_type', editor=EnumEditor(name='analysis_types')),
                   Item('standard_ratio'), show_border=True, label='IC')
        s = VGroup(HGroup(Item('marker', editor=EnumEditor(values=marker_names)),
                          Item('marker_size')), show_border=True, label='Scatter')
        y = VGroup(HGroup(Item('ymin', label='Min'),
                          Item('ymax', label='Max')), show_border=True, label='Y Limits')

        v = View(VGroup(f, s, y))
        return v
        # return View(VGroup(
        #     Item('numerator', editor=EnumEditor(name='detectors')),
        #     Item('denominator', editor=EnumEditor(name='detectors')),
        #
        #                 HGroup(Item('ymin', label='Min'),
        #                        Item('ymax', label='Max'),
        #                        show_border=True,
        #                        label='Y Limits'),
        #                 show_border=True))

    def _get_columns(self):
        return [
            object_column(name='numerator', editor=EnumEditor(name='detectors')),
            object_column(name='denominator', editor=EnumEditor(name='detectors')),
            checkbox_column(name='enabled', label='Plot'),
            checkbox_column(name='use', label='Save'),

            object_column(name='fit',
                          editor=EnumEditor(name='fit_types'),
                          width=75),
            object_column(name='error_type',
                          editor=EnumEditor(name='error_types'),
                          width=75, label='Error'),
            # checkbox_column(name='filter_outliers', label='Out.'),
            # object_column(name='filter_outlier_iterations', label='Iter.'),
            # object_column(name='filter_outlier_std_devs', label='SD'),
            # object_column(name='truncate', label='Trunc.'),
            # checkbox_column(name='include_baseline_error', label='Inc. BsErr')
        ]

# ============= EOF =============================================
