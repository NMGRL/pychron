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
from __future__ import absolute_import
from traits.api import Str, Float, Property, List

from pychron.options.fit import FitAuxPlot
from pychron.options.views.icfactor_views import VIEWS
from pychron.options.series import SeriesOptions
from pychron.pychron_constants import FIT_TYPES_INTERPOLATE, NULL_STR
from six.moves import range


class ICFactorAuxPlot(FitAuxPlot):
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

        return list(ANALYSIS_MAPPING.values())

    def _get_name(self):
        if self.denominator and self.denominator != NULL_STR:
            ret = '{}/{}'.format(self.numerator, self.denominator)
        else:
            ret = self.numerator
        return ret

    def _get_fit_types(self):
        return FIT_TYPES_INTERPOLATE


class ICFactorOptions(SeriesOptions):
    aux_plot_klass = ICFactorAuxPlot
    subview_names = List(['Main', 'ICFactor', 'Appearance'])

    def set_detectors(self, dets):
        dets = [NULL_STR, 'age'] + dets
        super(ICFactorOptions, self).set_detectors(dets)

    def get_subview(self, name):
        name = name.lower()
        klass = self._get_subview(name)
        obj = klass(model=self)
        return obj

    def _get_subview(self, name):
        return VIEWS[name]

    def set_aux_plots(self, ps):
        # for p in self.aux_plots:
        #     r = []
        #     for pd in ps:
        #         if p.numerator == pd.get('numerator') and p.denominator == pd.get('denominator'):
        #             r.append(pd)
        #     for ri in r:
        #         ps.remove(ri)
        #
        pp = [self.aux_plot_klass(**pd) for pd in ps]

        n = 5 - len(pp)
        if n:
            pp.extend((self.aux_plot_klass() for i in range(n)))

        self.aux_plots = pp
        self.selected = []

# ============= EOF =============================================
