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

from traits.api import Str, Int, Bool, List

from pychron.core.fits.fit import Fit
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.aux_plot import AuxPlot
from pychron.options.options import AuxPlotFigureOptions
from pychron.pychron_constants import FIT_ERROR_TYPES


class FitAuxPlot(AuxPlot, Fit):
    pass


class FitOptions(AuxPlotFigureOptions):
    global_fit = Str('Fit')
    global_error_type = Str('Error')
    nsigma = Int(1)
    use_time_axis = Bool(True)
    analysis_types = List
    available_types = List
    reference_types = List

    def set_names(self, names, clear_missing=True):
        for ai in self.aux_plots:
            if clear_missing and ai.name not in names:
                ai.plot_enabled = False
                ai.save_enabled = False
                ai.name = ''
            ai.names = names

    def set_detectors(self, dets):
        for p in self.aux_plots:
            p.detectors = dets

    def set_analysis_types(self, atypes):
        self.analysis_types = atypes[:]
        self.available_types = atypes

    def set_reference_types(self, atypes):
        self.reference_types = atypes[:]

    def _get_aux_plots(self):
        fs = self.selected_aux_plots
        if not fs:
            fs = self.aux_plots
        return fs

    def _global_fit_changed(self):
        # if self.global_fit in self.fit_types:
        fs = self._get_aux_plots()
        for fi in fs:
            fi.fit = self.global_fit

    def _global_error_type_changed(self):
        if self.global_error_type in FIT_ERROR_TYPES:
            fs = self._get_aux_plots()
            for fi in fs:
                fi.error_type = self.global_error_type

# ============= EOF =============================================
