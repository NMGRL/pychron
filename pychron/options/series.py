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

from traits.api import Bool, Enum

from pychron.options.fit import FitAuxPlot, FitOptions
from pychron.options.views.series_views import VIEWS
from pychron.pychron_constants import MAIN, APPEARANCE


class SeriesFitAuxPlot(FitAuxPlot):
    use_dev = Bool
    use_percent_dev = Bool

    def _use_dev_changed(self, new):
        if new:
            if self.use_percent_dev:
                self.use_percent_dev = False

    def _use_percent_dev_changed(self, new):
        if new:
            if self.use_dev:
                self.use_dev = False

    @property
    def filter_outliers_dict(self):
        return {}


class SeriesOptions(FitOptions):
    aux_plot_klass = SeriesFitAuxPlot
    error_bar_nsigma = Enum(1, 2, 3)
    end_caps = Bool(False)
    show_info = Bool(True)
    show_statistics = Bool(False)
    link_plots = Bool(True)

    # use_restricted_references = Bool
    def initialize(self):
        self.subview_names = [MAIN, 'Series', APPEARANCE]

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
