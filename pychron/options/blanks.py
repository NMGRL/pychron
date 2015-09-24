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
from traits.api import List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.blanks_views import VIEWS
from pychron.options.series import SeriesOptions, SeriesFitAuxPlot
from pychron.processing.fits.fit import FilterFit


class BlanksFitAuxPlot(SeriesFitAuxPlot, FilterFit):
    @property
    def filter_outliers_dict(self):
        return {'filter_outliers': self.filter_outliers,
                'iterations': self.filter_outlier_iterations,
                'std_devs': self.filter_outlier_std_devs}


class BlanksOptions(SeriesOptions):
    subview_names = List(['Main', 'Blanks', 'Appearance'])
    aux_plot_klass = BlanksFitAuxPlot
    # _main_options_klass = BlanksMainOptions

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
