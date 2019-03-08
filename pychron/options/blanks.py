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
from traits.api import Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.fits.fit import FilterFit
from pychron.options.series import SeriesOptions, SeriesFitAuxPlot
from pychron.options.views.blanks_views import VIEWS
from pychron.pychron_constants import MAIN, APPEARANCE


class BlanksFitAuxPlot(SeriesFitAuxPlot, FilterFit):
    def set_reference_types(self, atypes):
        for a in atypes:
            self.add_trait('ref_{}'.format(a.lower().replace(' ', '_')), Bool)

    @property
    def analysis_types(self):
        atypes = []
        for k,v in self.traits().items():
            if k.startswith('ref_') and getattr(self, k):
                atypes.append(k[4:])
        return atypes

    @property
    def filter_outliers_dict(self):
        return {'filter_outliers': self.filter_outliers,
                'iterations': self.filter_outlier_iterations,
                'std_devs': self.filter_outlier_std_devs,
                'use_standard_deviation_filtering': self.use_standard_deviation_filtering}


class BlanksOptions(SeriesOptions):
    aux_plot_klass = BlanksFitAuxPlot
    # _main_options_klass = BlanksMainOptions

    def initialize(self):
        self.subview_names = [MAIN, 'Blanks', APPEARANCE, 'Fit Matrix']

    def set_reference_types(self, atypes):
        super(BlanksOptions, self).set_reference_types(atypes)
        for a in self.aux_plots:
            a.set_reference_types(atypes)

    def _get_subview(self, name):
        return VIEWS[name]


# ============= EOF =============================================
