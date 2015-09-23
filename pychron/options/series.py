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
from pychron.options.fit import FitAuxPlot, FitOptions
from pychron.options.series_views import VIEWS
from pychron.pychron_constants import FIT_TYPES


class SeriesFitAuxPlot(FitAuxPlot):
    def _get_fit_types(self):
        return FIT_TYPES

    @property
    def filter_outliers_dict(self):
        return {}


class SeriesOptions(FitOptions):
    aux_plot_klass = SeriesFitAuxPlot
    subview_names = List(['Main', 'Series', 'Appearance'])

    def _get_subview(self, name):
        return VIEWS[name]

        # def _aux_plots_default(self):
        #     def f(kii):
        #         ff = self.aux_plot_klass(name=kii)
        #         ff.trait_set(plot_enabled=False,
        #                      save_enabled=False, fit='')
        #
        #         return ff
        #
        #     keys = list(ARGON_KEYS)
        #     keys.extend(['{}bs'.format(ki) for ki in ARGON_KEYS])
        #     keys.extend(['{}ic'.format(ki) for ki in ARGON_KEYS])
        #     if 'Ar40' in keys:
        #         if 'Ar39' in keys:
        #             keys.append('Ar40/Ar39')
        #             keys.append('uAr40/Ar39')
        #         if 'Ar36' in keys:
        #             keys.append('Ar40/Ar36')
        #             keys.append('uAr40/Ar36')
        #
        #     keys.append('Peak Center')
        #     keys.append('AnalysisType')
        #     return [f(k) for k in keys]

# ============= EOF =============================================
