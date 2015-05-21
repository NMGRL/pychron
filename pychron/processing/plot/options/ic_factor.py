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
from pychron.processing.fits.fit import Fit
from pychron.processing.plot.options.fit import FitOptions
from pychron.processing.plot.options.option import AuxPlotOptions
from pychron.pychron_constants import FIT_TYPES_INTERPOLATE


class ICFactorAuxPlot(AuxPlotOptions, Fit):
    names = List(['Ar40/Ar36', ])

    def _get_fit_types(self):
        return FIT_TYPES_INTERPOLATE


class ICFactorOptions(FitOptions):
    plot_option_klass = ICFactorAuxPlot

# ============= EOF =============================================
